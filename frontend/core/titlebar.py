from PySide6.QtCore import QSize
from PySide6.QtGui import QMouseEvent, QAction, Qt
from PySide6.QtWidgets import QLabel, QPushButton, QMenu, QHBoxLayout, QWidget

from frontend import AppCntxt


class CustomTitleBar(QWidget):
    """Custom titlebar with Windows-like buttons and drag/move."""
    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self._press_pos = None
        self._icon_size = 20

        self.setFixedHeight(32)
        self.setObjectName("CustomTitleBar")

        # icon + title
        self.icon = QLabel()
        self.icon.setFixedSize(30, 30)
        self.icon.setPixmap(AppCntxt.styler.get_pixmap('logo', AppCntxt.styler.get_colour('accent'), 28))

        self.btn_min = QPushButton("")
        self.btn_max = QPushButton("")
        self.btn_close = QPushButton("")

        self.btn_min.setIcon(AppCntxt.styler.get_pixmap('minimize', AppCntxt.styler.get_colour('accent_d3'), self._icon_size))
        self.btn_max.setIcon(AppCntxt.styler.get_pixmap('expand', AppCntxt.styler.get_colour('accent_d3'), self._icon_size))
        self.btn_close.setIcon(AppCntxt.styler.get_pixmap('close', AppCntxt.styler.get_colour('accent_d3'), self._icon_size))

        self.title = QLabel(parent.windowTitle())
        self.title.setObjectName("TitleLabel")
        self.title.setFont(AppCntxt.font.get_font('h2'))
        self.title.setStyleSheet(f"color: {AppCntxt.styler.get_colour('accent')}")

        # buttons

        for b in (self.btn_min, self.btn_max, self.btn_close):
            # b.setFixedSize(46, 28)
            # b.setFlat(True)
            b.setStyleSheet(f"background-color: transparent; border-radius: 2px;"
                            f"border: 1px solid {AppCntxt.styler.get_colour('bg1')}; "
                            f"margin-right: 4px;")
            b.setIconSize(QSize(self._icon_size, self._icon_size))

        self.btn_min.clicked.connect(parent.showMinimized)
        self.btn_max.clicked.connect(self._toggle_max)
        self.btn_close.clicked.connect(parent.close)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 0, 0, 0)
        lay.setSpacing(6)
        lay.addWidget(self.icon)
        lay.addWidget(self.title)
        lay.addStretch()
        lay.addWidget(self.btn_min)
        lay.addWidget(self.btn_max)
        lay.addWidget(self.btn_close)
        self.btn_close.setObjectName("close")

    def _toggle_max(self):
        if self._parent.isMaximized():
            self._parent.showNormal()
            self.btn_max.setIcon(AppCntxt.styler.get_pixmap('expand',
                                                            AppCntxt.styler.get_colour('accent_d3'),
                                                            self._icon_size))
        else:
            self._parent.showMaximized()
            self.btn_max.setIcon(AppCntxt.styler.get_pixmap('collapse',
                                                            AppCntxt.styler.get_colour('accent_d3'),
                                                            self._icon_size))

    # --- mouse events to drag the window ---
    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._press_pos = e.globalPosition().toPoint() - self._parent.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e: QMouseEvent):
        if e.buttons() & Qt.LeftButton and self._press_pos and not self._parent.isMaximized():
            self._parent.move(e.globalPosition().toPoint() - self._press_pos)
            e.accept()

    def mouseDoubleClickEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._toggle_max()

    def contextMenuEvent(self, e):
        m = QMenu(self)
        for text, slot in (
            ("Restore", self._parent.showNormal),
            ("Minimize", self._parent.showMinimized),
            ("Maximize", self._parent.showMaximized),
            ("Close", self._parent.close),
        ):
            act = QAction(text, m)
            act.triggered.connect(slot)
            m.addAction(act)
        m.exec(e.globalPos())