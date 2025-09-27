import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont

from common.logger import Logger
from common.stylemanager import StyleManager
from frontend import AppCntxt
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

        self.ui.app_name_label.setText(self.app_name)
        self.ui.version_label.setText(self.version)

        logger = Logger()
        # logger.log_updated.connect(self._on_log_updated)

        AppCntxt.data.register_progressbar(self.ui.progress_bar)
        AppCntxt.data.progress_changed.connect(self.set_progress)

        self.setPalette(AppCntxt.styler.get_palette())
        self.setFont(AppCntxt.font.get_font('pc'))
        self.ui.app_name_label.setFont(AppCntxt.font.get_font('h1'))
        self.ui.app_name_label.setStyleSheet(f"color: {AppCntxt.styler.get_colour('accent')}")
        # self.ui.progress_bar.setRange(0, 0)

        self.ui.logo_label.setPixmap(AppCntxt.styler.get_pixmap('logo',
                                                                AppCntxt.styler.get_colour('accent'),
                                                                100))
        style = f"""
QProgressBar {{
    background-color: {AppCntxt.styler.get_colour('bg1')};
    color: {AppCntxt.styler.get_colour('accent')}; /* text color */
}}

QProgressBar::chunk {{
    background-color: {AppCntxt.styler.get_colour('accent')};
    border-radius: 5px;
}}
"""
        self.ui.progress_bar.setStyleSheet(style)
        self.ui.progress_bar.setMaximumHeight(5)



    def set_progress(self, value=-1, message=None):
        if value != -1:
            self.ui.progress_bar.setValue(value)
        if message:
            self.ui.status_label.setText(message)
        QApplication.processEvents()  # Update UI immediately

    def _on_log_updated(self, data):
        if 'DEBUG' in data:
            return
        self.set_progress(-1, data)
