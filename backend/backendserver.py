import socket
import threading
import json
import inspect

from common.logger import Logger


class BackendServer:
    """
    A TCP server to expose SDK functions/classes to GUI clients.
    """

    def __init__(self, host="127.0.0.1", port=5000):
        self.host = host
        self.port = port
        self._server_socket = None
        self._running = False
        self._functions = {}
        self._logger = Logger()

    def register_function(self, func, name=None):
        """
        Register a standalone function.
        """
        self._functions[name or func.__name__] = func

    def register_instance(self, instance, prefix=""):
        """
        Register all public methods of a class instance.
        Example: prefix="math" → call("math.add", 2, 3)
        """
        for name, method in inspect.getmembers(instance, predicate=inspect.ismethod):
            if not name.startswith("_"):
                key = f"{prefix}.{name}" if prefix else name
                self._functions[key] = method

    def _handle_client(self, conn, addr):
        self._logger.debug(f"Backend server connection from {addr}")
        with conn:
            while True:
                try:
                    data = conn.recv(8192).decode("utf-8")
                    if not data:
                        break

                    request = json.loads(data)
                    func_name = request.get("function")
                    args = request.get("args", [])
                    kwargs = request.get("kwargs", {})
                    self._logger.debug(f"Backend server exec function: {func_name}")

                    if func_name in self._functions:
                        try:
                            result = self._functions[func_name](*args, **kwargs)
                            response = {"status": "ok", "result": result}
                        except Exception as e:
                            response = {"status": "error", "message": str(e)}
                    else:
                        response = {
                            "status": "error",
                            "message": f"Unknown function '{func_name}'",
                        }

                    conn.sendall(json.dumps(response).encode("utf-8"))
                except Exception as e:
                    error_msg = {"status": "error", "message": str(e)}
                    try:
                        conn.sendall(json.dumps(error_msg).encode("utf-8"))
                    except Exception:
                        pass
                    break

    def start(self):
        """Start the server in a background thread"""
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen()
        self._running = True

        def run():
            self._logger.debug(f"Backend server started on {self.host}:{self.port}")
            while self._running:
                try:
                    conn, addr = self._server_socket.accept()
                    thread = threading.Thread(
                        target=self._handle_client, args=(conn, addr), daemon=True
                    )
                    thread.start()
                except OSError:
                    break

        threading.Thread(target=run, daemon=True).start()

    def stop(self):
        """Stop the server"""
        self._running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
            self._server_socket = None
        print("[TCP SERVER] Stopped")
