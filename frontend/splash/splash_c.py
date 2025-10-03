from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget

from frontend import AppCntxt
from frontend.splash.splash import Ui_Splash


class Splash(QWidget):
    def __init__(self, app_name, version):
        super().__init__()
        self.ui = Ui_Splash()
        self.ui.setupUi(self)
        self.app_name = app_name
        self.version = version

        self._setup_window()
        self._setup_labels()
        self._setup_progress_bar()

        AppCntxt.data.register_progressbar(self.ui.progress_bar)
        AppCntxt.data.progress_changed.connect(self.set_progress)

    def _setup_window(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(600, 300)
        self.setPalette(AppCntxt.styler.get_palette())
        self.setFont(AppCntxt.font.get_font('pc'))

    def _setup_labels(self):
        self.ui.app_name_label.setText(self.app_name)
        self.ui.version_label.setText(self.version)
        self.ui.app_name_label.setFont(AppCntxt.font.get_font('h1'))
        self.ui.app_name_label.setStyleSheet(f"color: {AppCntxt.styler.get_colour('accent')}")
        self.ui.logo_label.setPixmap(AppCntxt.styler.get_pixmap('logo', AppCntxt.styler.get_colour('support'), 100))

    def _setup_progress_bar(self):
        style = f"""
        QProgressBar {{
            background-color: {AppCntxt.styler.get_colour('bg1')};
            color: {AppCntxt.styler.get_colour('neutral')};
        }}
        QProgressBar::chunk {{
            background-color: {AppCntxt.styler.get_colour('neutral')};
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
        QApplication.processEvents()
