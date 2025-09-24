from backend.backendserver import BackendServer

SERVER = BackendServer()
# Example SDK class
class MathSDK:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b


def run():
    global SERVER

    # Register individual function
    def hello(name):
        return f"Hello, {name}!"

    SERVER.register_function(hello)
    math = MathSDK()
    SERVER.register_instance(math, prefix="math")
    SERVER.start()

def stop():
    global SERVER
    SERVER.stop()