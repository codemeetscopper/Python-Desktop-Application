import hashlib

from backend.backendserver import BackendServer
from backend.sdk import SDK

SECRET_KEY = hashlib.sha256(b"sample key").digest()
SERVER = BackendServer(secret_key=SECRET_KEY)


def run():
    # Register individual function
    def hello(name):
        return f"Hello, {name}!"

    SERVER.register_function(hello)
    sdk = SDK()
    SERVER.register_instance(sdk, prefix="sdk")
    SERVER.start()


def stop():
    SERVER.stop()
