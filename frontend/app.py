import asyncio
import sys

from PySide6.QtWidgets import QApplication

from common.configuration.parser import ConfigurationManager
from common.logger import Logger
from frontend import ApplicationContext
from common import threadmanager
from common.backendmanager import BackendManager
from frontend.mainwindow.mainwindow_c import MainWindow
from frontend.splash.splash_c import Splash


def run():
    app = QApplication(sys.argv)
    _initialise_context()
    ApplicationContext.logger.info("Welcome!")

    splash = Splash(ApplicationContext.name, ApplicationContext.version)
    splash.show()
    _initialise_app()

    window = MainWindow()
    window.window_closing.connect(_on_app_closing)
    window.show()
    splash.close()
    sys.exit(app.exec())

def _initialise_context():
    ApplicationContext.logger = Logger()
    ApplicationContext.thread_manager = threadmanager.get_instance()
    ApplicationContext.settings = ConfigurationManager(ApplicationContext.config_path)

    ip = ApplicationContext.settings.get_value('sdk_ip_address')
    port = ApplicationContext.settings.get_value('sdk_tcp_port')

    ApplicationContext.sdk_manager = BackendManager(ip, port)
    QApplication.processEvents()

def _initialise_app():
    ApplicationContext.thread_manager.start()
    _backend_worker_demo()

def _on_app_closing():
    ApplicationContext.logger.info("Cleaning up...")
    if ApplicationContext.thread_manager is not None:
        ApplicationContext.thread_manager.shutdown()
    ApplicationContext.logger.info("Goodbye!")

def _backend_worker_demo():
    def on_log_update(data):
        ApplicationContext.logger.info(data)

    ApplicationContext.thread_manager.on("backend_log_update", on_log_update)

    async def non_blocking_work(n):
        with ApplicationContext.thread_manager.token():
            for i in range(n):
                QApplication.processEvents()
                ApplicationContext.thread_manager.emit('backend_log_update', f"Non blocking delay {str(i)}")
                await asyncio.sleep(0.001)
                # time.sleep(1)
    f = ApplicationContext.thread_manager.run_async(non_blocking_work(100))
    # f.result() # For waiting

    # def blocking_work(n):
    #     with ApplicationContext.thread_manager.token():
    #         time.sleep(n)
    #         ApplicationContext.logger.info(f"blocking delay {str(n)}")
    #
    # futures = [ApplicationContext.thread_manager.submit_blocking(blocking_work, i) for i in range(5)]
    #
    # # wait for all to finish
    # for f in futures:
    #     f.result()
