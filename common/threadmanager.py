"""
backend_interface.py

A sophisticated backend interface layer for a desktop application.

Features:
- Singleton Backend with get_instance()
- Runs an asyncio event loop in a dedicated background thread
- Uses a ThreadPoolExecutor for blocking/CPU tasks
- Uses a token-based Semaphore to limit concurrent worker threads ("tokens")
- Safe scheduling from GUI/main thread (both sync and async callables)
- Emits simple events via callback registration
- Graceful startup / shutdown

Design notes:
- This is intended to be embedded in a PySide/Qt desktop app where the GUI runs on the main thread
  and the Backend handles async / threaded work safely.
- You may expand the event system into a full signal/slot system or use libraries like pyee.

"""
from __future__ import annotations

import asyncio
import concurrent.futures
import inspect
import logging
import threading
import time
from contextlib import contextmanager
from typing import Any, Callable, Coroutine, Dict, Optional

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class BackendError(RuntimeError):
    pass


class _SingletonMeta:
    """Tiny singleton helper via attribute on the function module-level."""


_backend_instance: Optional["ThreadManager"] = None


def get_instance() -> "ThreadManager":
    """Return the shared Backend singleton (creates if missing).

    Use this in your application as the single access point for background tasks.
    """
    global _backend_instance
    if _backend_instance is None:
        _backend_instance = ThreadManager()
    return _backend_instance


class Token:
    """Context manager representing a concurrency token.

    Acquire with `with backend.token():` or via `await backend.acquire_token_async()`
    (the latter returns an async context manager).
    """

    def __init__(self, backend: "ThreadManager"):
        self._backend = backend
        self._released = False

    def release(self) -> None:
        if not self._released:
            self._backend._token_semaphore.release()
            self._released = True
            logger.debug("Token released")

    def __enter__(self) -> "Token":
        # This is a blocking acquire
        logger.debug("Acquiring token (blocking)")
        self._backend._token_semaphore.acquire()
        logger.debug("Token acquired (blocking)")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()

    async def __aenter__(self) -> "Token":
        # Async acquire uses loop.run_in_executor to avoid blocking the event loop
        logger.debug("Acquiring token (async)")
        await self._backend._loop.run_in_executor(None, self._backend._token_semaphore.acquire)
        logger.debug("Token acquired (async)")
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self.release()


class ThreadManager:
    """Backend manager.

    Typical usage:
        backend = get_instance()
        backend.start()
        future = backend.run_async(my_coroutine())
        backend.shutdown()

    or schedule blocking call:
        backend.submit_blocking(my_blocking_fn, arg1, kw=val)

    Token-based concurrency control:
        with backend.token():
            # do synchronous work with reserved token

        async with backend.acquire_token_async():
            # do async work with reserved token

    """

    def __init__(self, *, max_workers: int = 4, max_tokens: int = 2):
        """Create the Backend. Call start() to spin up the loop and workers.

        Args:
            max_workers: number of threads for ThreadPoolExecutor
            max_tokens: number of concurrent "tokens" permitted for critical sections
        """
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self._started = threading.Event()
        self._shutdown = threading.Event()

        self._max_workers = max_workers
        self._max_tokens = max_tokens
        self._token_semaphore = threading.Semaphore(max_tokens)

        # lightweight event/callback registry
        self._callbacks: Dict[str, Callable[..., None]] = {}

        # Lock for internal state
        self._state_lock = threading.RLock()

        logger.info("Backend created (max_workers=%s, max_tokens=%s)", max_workers, max_tokens)

    # ---------------- lifecycle -----------------
    def start(self) -> None:
        """Start the backend: create executor and run loop in background thread.

        This method is safe to call multiple times; subsequent calls are no-ops.
        """
        with self._state_lock:
            if self._started.is_set():
                logger.debug("Backend.start() called but already started")
                return

            self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers)

            # Create and run a new event loop in a dedicated thread
            def _run_loop() -> None:
                # Each thread must set its own event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                self._loop = loop
                logger.info("Backend event loop starting in thread %s", threading.current_thread().name)
                self._started.set()
                try:
                    loop.run_forever()
                finally:
                    loop.close()
                    logger.info("Backend event loop closed")

            self._loop_thread = threading.Thread(target=_run_loop, name="BackendLoopThread", daemon=True)
            self._loop_thread.start()

            # wait until loop is set up
            started = self._started.wait(timeout=5.0)
            if not started:
                raise BackendError("Failed to start backend event loop")

            # mark shutdown flag cleared
            self._shutdown.clear()
            logger.info("Backend started")

    def is_running(self) -> bool:
        return self._started.is_set() and not self._shutdown.is_set()

    def shutdown(self, wait: bool = True) -> None:
        with self._state_lock:
            if not self._started.is_set() or self._loop is None:
                return

            logger.info("Shutting down backend")

            try:
                fut = asyncio.run_coroutine_threadsafe(self._async_shutdown(), self._loop)
                try:
                    fut.result(timeout=3)  # shorter timeout
                except concurrent.futures.TimeoutError:
                    logger.warning("Async shutdown timed out; forcing loop stop")
                    self._shutdown.set()
                    self._loop.call_soon_threadsafe(self._loop.stop)
            except RuntimeError:
                logger.exception("Error while stopping backend loop")

            if self._executor:
                self._executor.shutdown(wait=wait)
                self._executor = None

            if self._loop_thread:
                self._loop_thread.join(timeout=5.0)
                self._loop_thread = None

            self._loop = None
            self._started.clear()
            logger.info("Backend shutdown complete")

    async def _async_shutdown(self) -> None:
        # Cancel tasks except the current one
        current = asyncio.current_task()
        tasks = [t for t in asyncio.all_tasks(loop=self._loop) if t is not current]
        for t in tasks:
            t.cancel()

        # Allow cancellations to propagate
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:
            pass

        self._shutdown.set()
        self._loop.stop()

    # ---------------- scheduling -----------------
    def run_async(self, coro: Coroutine) -> concurrent.futures.Future:
        """Schedule a coroutine to run on the backend event loop from any thread.

        Returns a concurrent.futures.Future that can be waited on from the caller thread.
        """
        if not self._started.is_set() or self._loop is None:
            raise BackendError("Backend not started. Call start() before scheduling tasks.")

        if not inspect.iscoroutine(coro):
            raise TypeError("run_async expects a coroutine object")

        logger.debug("Scheduling coroutine on backend loop")
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def submit_blocking(self, fn: Callable[..., Any], *args, **kwargs) -> concurrent.futures.Future:
        """Submit a blocking function to the thread pool executor.

        If the backend is not started we start it automatically.
        """
        if not self._started.is_set():
            self.start()

        if self._executor is None:
            raise BackendError("ThreadPoolExecutor is not available")

        logger.debug("Submitting blocking function to executor: %s", fn)
        return self._executor.submit(fn, *args, **kwargs)

    # ---------------- tokens -----------------
    @contextmanager
    def token(self) -> Token:
        """Blocking context manager to acquire a concurrency token.

        Example:
            with backend.token():
                # critical section limited by tokens
        """
        t = Token(self)
        try:
            with t:
                yield t
        finally:
            # ensure token released
            if not getattr(t, "_released", True):
                t.release()

    def acquire_token(self, timeout: Optional[float] = None) -> bool:
        """Try to acquire a token in a blocking fashion with optional timeout.

        Returns True if acquired, False otherwise.
        """
        return self._token_semaphore.acquire(timeout=timeout)

    def release_token(self) -> None:
        self._token_semaphore.release()

    async def acquire_token_async(self, timeout: Optional[float] = None) -> Token:
        """Return an async Token context manager after acquiring a token asynchronously.

        Usage:
            async with await backend.acquire_token_async():
                ...
        """
        # If timeout is provided, implement via loop.run_in_executor polling
        if timeout is None:
            t = Token(self)
            # __aenter__ will await acquisition
            await t.__aenter__()
            return t

        # implement timeout by running blocking acquire in executor
        loop = asyncio.get_running_loop()
        acquired = await loop.run_in_executor(None, lambda: self._token_semaphore.acquire(timeout=timeout))
        if not acquired:
            raise asyncio.TimeoutError("Timeout while waiting for token")
        return Token(self)

    # ---------------- events / callbacks -----------------
    def on(self, name: str, callback: Callable[..., None]) -> None:
        """Register a callback for a named event. Overwrites existing callback with same name.

        Example events might be: 'initialise_done', 'task_complete'
        """
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._callbacks[name] = callback

    def emit(self, name: str, *args, **kwargs) -> None:
        """Emit an event by calling the registered callback. Called from any thread.

        If a callback was registered it will be invoked in the thread that calls emit().
        If you need the callback executed on the backend loop, schedule it with run_async.
        """
        cb = self._callbacks.get(name)
        if cb:
            try:
                cb(*args, **kwargs)
            except Exception:
                logger.exception("Event callback %r raised", name)

    # ---------------- utility helpers -----------------
    def run_coroutine_blocking(self, coro: Coroutine, timeout: Optional[float] = None) -> Any:
        """Convenience: schedule a coroutine on the backend loop and block until it's done.

        This is safe to call from the main thread.
        """
        fut = self.run_async(coro)
        return fut.result(timeout=timeout)


# ---------------- example usage -----------------
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    backend = get_instance()
    backend.start()

    # register a callback
    def on_init_done(ok: bool):
        print("initialise_done ->", ok)

    backend.on("initialise_done", on_init_done)

    # Example: async initialise task
    async def initialise():
        print("initialise: sleeping 1s")
        await asyncio.sleep(1)
        backend.emit("initialise_done", True)
        return True

    # Schedule initialise and wait for result
    res = backend.run_coroutine_blocking(initialise(), timeout=5)
    print("initialise result:", res)

    # Example: use token to limit simultaneous blocking tasks
    def blocking_work(n):
        with backend.token():
            print(f"Worker {n} acquired token, working...")
            time.sleep(1)
            print(f"Worker {n} done")

    futures = [backend.submit_blocking(blocking_work, i) for i in range(6)]

    # wait for all to finish
    for f in futures:
        f.result()

    backend.shutdown()
    print("backend stopped")
