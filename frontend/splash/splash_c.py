import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont

from common.logger import Logger
from frontend.splash.splash import Ui_Splash


class Splash(QWidget):
    def __init__(self, app_name, version):
        super().__init__()
        self.ui = Ui_Splash()
        self.ui.setupUi(self)
        self.app_name = app_name
        self.version = version

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(600, 300)  # Customize as needed

        # pixmap = QPixmap("splash_image.png")  # Put your image path here
        # self.ui.logo_label.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        # self.ui.logo_label.setGeometry(0, 0, 500, 300)

        # App Name
        self.ui.app_name_label.setText(self.app_name)
        self.ui.version_label.setText(self.version)

        logger = Logger()
        logger.log_updated.connect(self._on_log_updated)


    def set_progress(self, value=-1, status_text=None):
        if value != -1:
            self.ui.progress_bar.setValue(value)
        if status_text:
            self.ui.status_label.setText(status_text)
        QApplication.processEvents()  # Update UI immediately

    def _on_log_updated(self, data):
        if "DEBUG" in data:
            return
        self.set_progress(-1, data)
