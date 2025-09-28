import socket
import json
from common.tcpinterface.aes import AESCipher


class BackendClient:
    """
    A TCP client to call SDK functions exposed by BackendServer with AES encryption.
    """

    def __init__(self, host="127.0.0.1", port=5000, timeout=5, secret_key=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        if secret_key is None:
            raise ValueError("Secret key required for AES encryption")
        self._cipher = AESCipher(secret_key)

    def call(self, func_name, *args, **kwargs):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                s.connect((self.host, self.port))

                # 🔐 Encrypt request
                request = {"function": func_name, "args": args, "kwargs": kwargs}
                enc_request = self._cipher.encrypt(request)
                s.sendall(enc_request.encode("utf-8"))

                # 🔐 Decrypt response
                response = s.recv(8192).decode("utf-8")
                return self._cipher.decrypt(response)

        except Exception as e:
            return {"status": "error", "message": f"TCP backend comm failure: {str(e)}"}
