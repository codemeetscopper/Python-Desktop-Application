import backend.sdkmanager
import frontend.app

if __name__ == "__main__":
    backend.sdkmanager.run()
    frontend.app.run()
    backend.sdkmanager.stop()
