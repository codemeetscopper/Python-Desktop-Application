import socket
import json


class BackendClient:
    """
    A TCP client to call SDK functions exposed by TcpServer.
    """

    def __init__(self, host="127.0.0.1", port=5000, timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout

    def call(self, func_name, *args, **kwargs):
        """
        Call a function on the server.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                s.connect((self.host, self.port))

                request = {"function": func_name, "args": args, "kwargs": kwargs}
                s.sendall(json.dumps(request).encode("utf-8"))

                response = s.recv(8192).decode("utf-8")
                return json.loads(response)
        except Exception as e:
            return {"status": "error", "message": str(e)}