import socket
import threading
import logging

from common.logger import Logger


class BackendManager:
    """Manages TCP communication with the SDK server running on localhost."""

    def __init__(self, host='127.0.0.1', port=9000, timeout=5):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._sock = None
        self._lock = threading.Lock()
        self._logger = Logger()

    def connect(self):
        """Establish a TCP connection to the SDK server."""
        try:
            self._sock = socket.create_connection((self._host, self._port), timeout=self._timeout)
            self._logger.info(f"Connected to SDK server at {self._host}:{self._port}")
        except socket.error as e:
            self._logger.error(f"Connection failed: {e}")
            raise

    def disconnect(self):
        """Close the TCP connection."""
        if self._sock:
            try:
                self._sock.close()
                self._logger.info("Disconnected from SDK server.")
            except socket.error as e:
                self._logger.warning(f"Error while disconnecting: {e}")
            finally:
                self._sock = None

    def send_request(self, request: str) -> str:
        """Send a request to the SDK server and return the response."""
        if not self._sock:
            raise ConnectionError("Not connected to SDK server.")

        with self._lock:
            try:
                self._logger.debug(f"Sending request: {request}")
                self._sock.sendall(request.encode('utf-8') + b'\n')
                response = self._receive_response()
                self._logger.debug(f"Received response: {response}")
                return response
            except socket.error as e:
                self._logger.error(f"Communication error: {e}")
                raise

    def _receive_response(self) -> str:
        """Receive response from the SDK server."""
        chunks = []
        while True:
            chunk = self._sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            if b'\n' in chunk:
                break
        return b''.join(chunks).decode('utf-8').strip()

    def call_api(self, api_name: str, params: dict) -> str:
        """Format and send an API call to the SDK server."""
        request = f"{api_name} {params}"
        return self.send_request(request)
