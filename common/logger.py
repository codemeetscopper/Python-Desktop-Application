import logging
import functools
from datetime import datetime
from PySide6.QtCore import QObject, Signal


class Logger(QObject):
    """Singleton Qt Logger with in-memory storage, signal updates, and export feature."""
    _instance = None
    log_updated = Signal(str)  # Qt signal emitted when a new log entry is added

    def __new__(cls, *args, **kwargs):
        """Singleton pattern using __new__."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, name: str="Application", level=logging.INFO):
        if getattr(self, "_initialized", False):
            return  # Avoid reinitializing the singleton

        super().__init__()
        self.name = name
        self.level = level
        self.logs = []  # In-memory log storage

        # Setup Python logging
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        self._logger.propagate = False

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        console_handler.setFormatter(formatter)

        if not self._logger.handlers:
            self._logger.addHandler(console_handler)

        self._initialized = True

    def _store_log(self, level_name: str, msg: str):
        """Store log in memory and emit update signal."""
        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        formatted = f"{timestamp} | {level_name} | {msg}"
        self.logs.append(formatted)
        if level_name != "DEBUG":
            self.log_updated.emit(msg)
        else:
            print(formatted)
        return formatted

    # Logging methods
    def debug(self, msg, *args, **kwargs):
        formatted = self._store_log("DEBUG", msg)
        self._logger.debug(msg, *args, **kwargs)
        return formatted

    def info(self, msg, *args, **kwargs):
        formatted = self._store_log("INFO", msg)
        self._logger.info(msg, *args, **kwargs)
        return formatted

    def warning(self, msg, *args, **kwargs):
        formatted = self._store_log("WARNING", msg)
        self._logger.warning(msg, *args, **kwargs)
        return formatted

    def error(self, msg, *args, **kwargs):
        formatted = self._store_log("ERROR", msg)
        self._logger.error(msg, *args, **kwargs)
        return formatted

    def critical(self, msg, *args, **kwargs):
        formatted = self._store_log("CRITICAL", msg)
        self._logger.critical(msg, *args, **kwargs)
        return formatted

    # Decorator for function logging
    def log_function(self, level=logging.DEBUG):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if self._logger.isEnabledFor(level):
                    arg_list = [repr(a) for a in args] + [f"{k}={v!r}" for k, v in kwargs.items()]
                    call_msg = f"Calling {func.__name__}({', '.join(arg_list)})"
                    self._store_log(logging.getLevelName(level), call_msg)
                result = func(*args, **kwargs)
                if self._logger.isEnabledFor(level):
                    self._store_log(logging.getLevelName(level), f"{func.__name__} returned {result!r}")
                return result
            return wrapper

        return decorator

    # Export logs to a file
    def export_to_file(self, file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            for line in self.logs:
                f.write(line + "\n")

