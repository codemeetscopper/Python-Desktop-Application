from PySide6.QtCore import Qt, QPoint, QRect, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget
)

from common.configuration.parser import ConfigurationManager
from common.logger import Logger
from common import AppCntxt
from common.qwidgets.titlebar import CustomTitleBar
from frontend.mainwindow.mainwindow import Ui_MainWindow


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
        self.titlebar = CustomTitleBar(self)

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
            self.ui.statusbar.showMessage(log_text.split('| ')[-1])

    def closeEvent(self, event):
        self.destroy()
        self.window_closing.emit()
        event.accept()
