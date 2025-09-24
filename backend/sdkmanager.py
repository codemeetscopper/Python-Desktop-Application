from backend.backendserver import BackendServer
from backend.sdk import SDK

SERVER = BackendServer()

def run():
    global SERVER
    # Register individual function
    def hello(name):
        return f"Hello, {name}!"

    SERVER.register_function(hello)
    sdk = SDK()
    SERVER.register_instance(sdk, prefix="sdk")
    SERVER.start()

def stop():
    global SERVER
    SERVER.stop()