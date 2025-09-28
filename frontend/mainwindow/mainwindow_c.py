from PySide6.QtCore import Qt, QPoint, QRect, Signal, QSize
from PySide6.QtGui import QMouseEvent, QAction
from PySide6.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget,
    QHBoxLayout, QPushButton, QMenu, QStyle
)

from common.configuration.parser import ConfigurationManager, LOGGER
from common.logger import Logger
from frontend import AppCntxt
from frontend.mainwindow.mainwindow import Ui_MainWindow


class TitleBar(QWidget):
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
        self.icon.setFixedSize(self._icon_size, self._icon_size)
        self.icon.setPixmap(AppCntxt.styler.get_pixmap('logo',
                                                       AppCntxt.styler.get_colour('accent'),
                                                       self._icon_size))

        self.btn_min = QPushButton("")
        self.btn_max = QPushButton("")
        self.btn_close = QPushButton("")

        self.btn_min.setIcon(AppCntxt.styler.get_pixmap('minimize',
                                                       AppCntxt.styler.get_colour('accent_d3'),
                                                       self._icon_size))
        self.btn_max.setIcon(AppCntxt.styler.get_pixmap('expand',
                                                       AppCntxt.styler.get_colour('accent_d3'),
                                                       self._icon_size))
        self.btn_close.setIcon(AppCntxt.styler.get_pixmap('close',
                                                       AppCntxt.styler.get_colour('accent_d3'),
                                                       self._icon_size))



        self.title = QLabel(parent.windowTitle())
        self.title.setObjectName("TitleLabel")
        self.title.setFont(AppCntxt.font.get_font('h2'))
        self.title.setStyleSheet(f"color: {AppCntxt.styler.get_colour('accent')}")

        # buttons

        for b in (self.btn_min, self.btn_max, self.btn_close):
            # b.setFixedSize(46, 28)
            # b.setFlat(True)
            b.setStyleSheet(f"background-color: transparent; border: none; margin: 3px;")
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


class MainWindow(QMainWindow):
    window_closing = Signal()

    EDGE_MARGIN = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        # remove native frame
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setMinimumSize(400, 250)

        self._config = ConfigurationManager()
        self._logger = Logger()
        self._logger.log_updated.connect(self._on_log_updated)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle(AppCntxt.name)
        self.titlebar = TitleBar(self)

        setting = "Settings:"
        for key in self._config.get_all_keys():
            val = self._config.get_value(key)
            v = val.value if hasattr(val, "value") else val
            setting += f"\n   {key} = {v}"

        label = QLabel(setting, self)
        content_layout = QVBoxLayout()
        content_layout.addWidget(label)

        container = QWidget()
        container.setLayout(content_layout)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.titlebar)
        layout.addWidget(container)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

        self._apply_style()

        # vars for resizing
        self._resizing = False
        self._resize_edge = None
        self._press_pos = QPoint()
        self._press_geo = QRect()

    # ---------- custom resizing ----------
    def _edge_at(self, pos):
        x, y, w, h, m = pos.x(), pos.y(), self.width(), self.height(), self.EDGE_MARGIN
        left, right, top, bottom = x <= m, x >= w - m, y <= m, y >= h - m
        if top and left: return "tl"
        if top and right: return "tr"
        if bottom and left: return "bl"
        if bottom and right: return "br"
        if left: return "l"
        if right: return "r"
        if top: return "t"
        if bottom: return "b"
        return None

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton and not self.isMaximized():
            edge = self._edge_at(e.pos())
            if edge:
                self._resizing = True
                self._resize_edge = edge
                self._press_pos = e.globalPosition().toPoint()
                self._press_geo = self.geometry()
                return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e: QMouseEvent):
        if self._resizing:
            self._perform_resize(e.globalPosition().toPoint())
            return
        cursors = {
            "l": Qt.SizeHorCursor, "r": Qt.SizeHorCursor,
            "t": Qt.SizeVerCursor, "b": Qt.SizeVerCursor,
            "tl": Qt.SizeFDiagCursor, "br": Qt.SizeFDiagCursor,
            "tr": Qt.SizeBDiagCursor, "bl": Qt.SizeBDiagCursor,
        }
        self.setCursor(cursors.get(self._edge_at(e.pos()), Qt.ArrowCursor))
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e: QMouseEvent):
        self._resizing = False
        self._resize_edge = None
        super().mouseReleaseEvent(e)

    def _perform_resize(self, gpos: QPoint):
        diff = gpos - self._press_pos
        geo = QRect(self._press_geo)
        if "l" in self._resize_edge: geo.setLeft(geo.left() + diff.x())
        if "r" in self._resize_edge: geo.setRight(geo.right() + diff.x())
        if "t" in self._resize_edge: geo.setTop(geo.top() + diff.y())
        if "b" in self._resize_edge: geo.setBottom(geo.bottom() + diff.y())
        if geo.width() >= self.minimumWidth() and geo.height() >= self.minimumHeight():
            self.setGeometry(geo)

    # ---------- keep your existing logic ----------
    def _apply_style(self):
        self.setPalette(AppCntxt.styler.get_palette())
        self.setFont(AppCntxt.font.get_font('p'))

    def _on_log_updated(self, log_text):
        if 'DEBUG' not in log_text:
            self.ui.statusbar.showMessage(log_text)

    def closeEvent(self, event):
        self.destroy()
        self.window_closing.emit()
        event.accept()
