from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget

from common.configuration.parser import ConfigurationManager, LOGGER
from common.logger import Logger
from frontend import AppCntxt
from frontend.mainwindow.mainwindow import Ui_MainWindow


class MainWindow(QMainWindow):
    window_closing = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._config = ConfigurationManager()
        self._logger = Logger()
        self._logger.log_updated.connect(self._on_log_updated)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)


        self.setWindowTitle("PySide6 MainWindow Example")

        setting = "Settings:"
        for key in self._config.get_all_keys():
            if hasattr(self._config.get_value(key), 'value'):
                setting = setting + '\n' + f"   {key} = {self._config.get_value(key).value}"
            else:
                setting = setting + f"\n    {key} = {self._config.get_value(key)}"

        # setting = f"Theme is {self._config.get_value("theme").value}\n"\
        #           f"Accent is {self._config.get_value("accent").value}\n"
        label = QLabel(setting, self)
        layout = QVBoxLayout()
        layout.addWidget(label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self._apply_style()

    def _apply_style(self):
        self.setPalette(AppCntxt.styler.get_palette())
        self.setFont(AppCntxt.font.get_font('p'))

    def _on_log_updated(self, log_text):
        if 'DEBUG' not in log_text:
            self.ui.statusbar.showMessage(log_text)

    def closeEvent(self, event):
        self.close()
        self.window_closing.emit()
        event.accept()