import asyncio
import hashlib
import sys
import time

from PySide6.QtWidgets import QApplication

from common import threadmanager
from common.tcpinterface.backendclient import BackendClient
from common.configuration.parser import ConfigurationManager
from common.appearance.fontmanager import FontManager
from common.logger import Logger
from common.appearance.stylemanager import StyleManager
from frontend import AppCntxt, AppData
from frontend.core.popup.popup_c import Popup
from frontend.mainwindow.mainwindow_c import MainWindow
from frontend.splash.splash_c import Splash


def run():
    app = QApplication(sys.argv)
    _initialise_context()
    AppCntxt.logger.info("Welcome!")

    splash = Splash(AppCntxt.name, f"Version {AppCntxt.version}")
    splash.show()
    AppCntxt.data.set_progress(5, "Initialising application...")
    QApplication.processEvents()
    status, error = _initialise_app()
    if status:
        window = MainWindow()
        window.window_closing.connect(_on_app_closing)
        window.show()
        AppCntxt.logger.info("Ready")

    if not status:
        Popup.show_popup("Failed to start",
                              f"The following error occurred:\n{error}\n",
                              mtype="error", parent=splash)
        _on_app_closing()
    splash.close()
    app.exec()

def _initialise_context():
    AppCntxt.logger = Logger()
    AppCntxt.threader = threadmanager.get_instance()

    AppCntxt.data = AppData()

    AppCntxt.threader.start()
    AppCntxt.settings = ConfigurationManager(AppCntxt.config_path)

    ip = AppCntxt.settings.get_value('sdk_ip_address')
    port = AppCntxt.settings.get_value('sdk_tcp_port')
    timeout = AppCntxt.settings.get_value('sdk_tcp_timeout')
    # key = AppCntxt.settings.get_value('sdk_aes_key')
    key = hashlib.sha256(b"sample key").digest()
    AppCntxt.backend = BackendClient(ip, port, timeout, secret_key = key)

    AppCntxt.styler = StyleManager()
    accent = AppCntxt.settings.get_value('accent')
    support = AppCntxt.settings.get_value('support')
    neutral = AppCntxt.settings.get_value('neutral')
    theme = AppCntxt.settings.get_value('theme')
    AppCntxt.styler.initialise(accent, support, neutral, theme)

    AppCntxt.font = FontManager()
    AppCntxt.font.load_font(r"resources/fonts/RobotoCondensed-VariableFont_wght.ttf", "h1", 18)
    AppCntxt.font.load_font(r"resources/fonts/RobotoCondensed-VariableFont_wght.ttf", "h2", 14)
    AppCntxt.font.load_font(r"resources/fonts/Roboto-VariableFont_wdth,wght.ttf", "p", 11)
    AppCntxt.font.load_font(r"resources/fonts/RobotoCondensed-VariableFont_wght.ttf", "pc", 11)
    AppCntxt.font.load_font(r"resources/fonts/Inconsolata-VariableFont_wdth,wght.ttf", "log", 11)
    QApplication.processEvents()

def _initialise_app():
    def initialise_backend():
        with AppCntxt.threader.token():
            result = AppCntxt.backend.call("sdk.initialise")
        if result['status'] == 'ok': return True, result['result']
        elif result['status'] == 'error': return False, result['message']
        return False, None
    api_reply = False
    error = None
    fb = AppCntxt.threader.submit_blocking(initialise_backend)
    AppCntxt.data.set_progress(10, "Connecting to backend...")
    while fb.running():
        # time.sleep(0.01)
        QApplication.processEvents()
    if fb.result()[0]:
        AppCntxt.logger.info("Backend initialisation is success")
        api_reply = True
    else:
        error = fb.result()[1]
        AppCntxt.logger.critical(f"Backend init failure: error: {error}")
        if 'WinError 10061' in error:
            AppCntxt.logger.critical(message:=f"Check if the backend is running. Address: {AppCntxt.backend.host}:{AppCntxt.backend.port}")
            error = error + '\n' + message
    # _backend_worker_demo()
    return api_reply, error

def _on_app_closing():
    splash = Splash(AppCntxt.name, f"Version {AppCntxt.version}")
    splash.show()
    AppData().set_progress(value=20, message=f"({20}%)  Cleaning up...")
    def cleanup():
        with AppCntxt.threader.token():
            time.sleep(1)
        return True
    fb = AppCntxt.threader.submit_blocking(cleanup)
    time.sleep(0.1)
    while fb.running():
        time.sleep(0.001)
        QApplication.processEvents()

    AppData().set_progress(value=95, message=f"({95}%)  Cleaning up...")
    fb.result()
    QApplication.processEvents()

    if AppCntxt.threader is not None:
        AppCntxt.threader.shutdown()
    splash.close()
    AppCntxt.logger.info("Goodbye!")
    sys.exit(0)

def _backend_worker_demo():
    def on_log_update(data):
        AppCntxt.logger.info(data)

    AppCntxt.threader.on("backend_log_update", on_log_update)

    async def non_blocking_work(n):
        with AppCntxt.threader.token():
            for i in range(n):
                QApplication.processEvents()
                AppCntxt.threader.emit('backend_log_update', f"Non blocking delay {str(i)}")
                await asyncio.sleep(0.1)
                # time.sleep(1)
    f = AppCntxt.threader.run_async(non_blocking_work(100))
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
