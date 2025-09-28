# custom_titlebar.py
# Run with: python custom_titlebar.py
# Requires: PySide6 (pip install PySide6)

from PySide6.QtCore import (
    Qt,
    QPoint,
    QRect,
    QSize,
)
from PySide6.QtGui import (
    QAction,
    QCursor,
    QIcon,
    QMouseEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QMainWindow,
    QSizeGrip,
    QMenu, QStyle,
)


class CustomTitleBar(QWidget):
    """
    Custom titlebar that mimics native Windows titlebar behaviour:
    - drag to move window
    - double click to maximize/restore
    - minimize/maximize/close buttons
    - right-click system menu
    """

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._parent = parent  # the frameless window
        self.setFixedHeight(32)  # titlebar height similar to Windows
        self._mouse_down = False
        self._drag_pos = QPoint()
        self._is_double_click = False

        # Icon (optional)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        # use a generic icon from style if available
        app_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)
        self.icon_label.setPixmap(app_icon.pixmap(24, 24))

        # Title
        self.title_label = QLabel(self._parent.windowTitle())
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        # Buttons
        self.btn_min = QPushButton("_")
        self.btn_max = QPushButton("⬜")  # will change glyph on maximize/restore
        self.btn_close = QPushButton("✕")

        for b in (self.btn_min, self.btn_max, self.btn_close):
            b.setFixedSize(46, 28)
            b.setFlat(True)
            b.setFocusPolicy(Qt.NoFocus)

        # Button signals
        self.btn_min.clicked.connect(self._parent.showMinimized)
        self.btn_max.clicked.connect(self.toggleMaxRestore)
        self.btn_close.clicked.connect(self._parent.close)

        # Right-click system menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showSystemMenu)

        # Layout
        hl = QHBoxLayout(self)
        hl.setContentsMargins(8, 0, 0, 0)
        hl.setSpacing(6)
        hl.addWidget(self.icon_label)
        hl.addWidget(self.title_label)
        hl.addStretch()
        hl.addWidget(self.btn_min)
        hl.addWidget(self.btn_max)
        hl.addWidget(self.btn_close)

        # Stylesheet: simple native-like look (light theme)
        self.setStyleSheet(
            """
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #F3F3F3, stop:1 #EDEDED);
            }
            #TitleLabel {
                color: #111;
                font-weight: 500;
            }
            QPushButton {
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                background: rgba(0,0,0,0.06);
            }
            QPushButton:pressed {
                background: rgba(0,0,0,0.12);
            }
            QPushButton#close:hover {
                background: #E81123;
                color: white;
            }
            """
        )

        # Make close button get a special object name for targeted style
        self.btn_close.setObjectName("close")

    def setTitle(self, text: str):
        self.title_label.setText(text)

    def toggleMaxRestore(self):
        if self._parent.isMaximized():
            self._parent.showNormal()
            self.btn_max.setText("⬜")
        else:
            self._parent.showMaximized()
            self.btn_max.setText("❐")

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        # double-click on titlebar toggles maximize/restore
        if event.button() == Qt.LeftButton:
            self.toggleMaxRestore()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._mouse_down = True
            self._drag_pos = event.globalPosition().toPoint() - self._parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._mouse_down and not self._parent.isMaximized():
            # move window based on delta
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self._parent.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._mouse_down = False
        event.accept()

    def _showSystemMenu(self, pos):
        menu = QMenu(self)
        act_restore = QAction("Restore", self)
        act_move = QAction("Move", self)
        act_size = QAction("Size", self)
        act_min = QAction("Minimize", self)
        act_max = QAction("Maximize", self)
        act_close = QAction("Close", self)

        act_restore.triggered.connect(lambda: self._parent.showNormal())
        act_min.triggered.connect(lambda: self._parent.showMinimized())
        act_max.triggered.connect(lambda: self._parent.showMaximized())
        act_close.triggered.connect(lambda: self._parent.close())

        menu.addAction(act_restore)
        menu.addAction(act_move)
        menu.addAction(act_size)
        menu.addSeparator()
        menu.addAction(act_min)
        menu.addAction(act_max)
        menu.addSeparator()
        menu.addAction(act_close)

        # show at cursor (translate local pos)
        menu.exec(QCursor.pos())


class FramelessWindow(QWidget):
    """
    Frameless window supporting custom titlebar and edge/corner resize grips.
    """

    _MARGIN = 6  # thickness in pixels for resize area detection

    def __init__(self):
        super().__init__(None, Qt.Window)
        self.setWindowTitle("Custom Titlebar - PySide6")
        self.setWindowFlag(Qt.FramelessWindowHint)
        # enable system menu on Windows when right-click or Alt+Space etc, but we provide custom menu
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Keep a minimal size
        self.setMinimumSize(320, 200)

        # Layout: vertical -> titlebar + content
        self.vbox = QVBoxLayout(self)
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.vbox.setSpacing(0)

        # TitleBar
        self.titlebar = TitleBar(self)
        self.vbox.addWidget(self.titlebar)

        # Central content for demo
        self.content = QLabel("Main content area\n\nTry: drag the title, double-click it, resize window from edges/corners, use buttons.")
        self.content.setAlignment(Qt.AlignCenter)
        self.content.setObjectName("contentLabel")
        self.content.setMinimumHeight(120)
        self.vbox.addWidget(self.content, 1)

        # Use status style for content
        self.setStyleSheet(
            """
            QLabel#contentLabel {
                background: white;
                padding: 12px;
                color: #222;
                font-size: 13px;
            }
            """
        )

        # Vars for resizing
        self._resizing = False
        self._resize_dir = None
        self._mouse_press_pos = QPoint()
        self._mouse_press_geo = QRect()

        # Keep title updated if windowTitle changes
        self.windowTitleChanged.connect(self.titlebar.setTitle)

    # ---------- Hit-testing for edges/corners ----------
    def _getEdgeAtPos(self, pos: QPoint):
        """
        Returns a string code for edge under the given local position:
        one of: 'left', 'right', 'top', 'bottom', 'top-left', 'top-right', 'bottom-left', 'bottom-right', or None
        """
        x = pos.x()
        y = pos.y()
        w = self.width()
        h = self.height()
        m = self._MARGIN

        left = x <= m
        right = x >= w - m
        top = y <= m
        bottom = y >= h - m

        if top and left:
            return "top-left"
        if top and right:
            return "top-right"
        if bottom and left:
            return "bottom-left"
        if bottom and right:
            return "bottom-right"
        if left:
            return "left"
        if right:
            return "right"
        if top:
            return "top"
        if bottom:
            return "bottom"
        return None

    def _setCursorForEdge(self, edge: str):
        mapping = {
            "left": Qt.SizeHorCursor,
            "right": Qt.SizeHorCursor,
            "top": Qt.SizeVerCursor,
            "bottom": Qt.SizeVerCursor,
            "top-left": Qt.SizeFDiagCursor,
            "bottom-right": Qt.SizeFDiagCursor,
            "top-right": Qt.SizeBDiagCursor,
            "bottom-left": Qt.SizeBDiagCursor,
            None: Qt.ArrowCursor,
        }
        q = mapping.get(edge, Qt.ArrowCursor)
        self.setCursor(q)

    # ---------- Mouse events for resizing ----------
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            local_pos = event.position().toPoint()
            edge = self._getEdgeAtPos(local_pos)
            if edge and not self.isMaximized():
                self._resizing = True
                self._resize_dir = edge
                self._mouse_press_pos = event.globalPosition().toPoint()
                self._mouse_press_geo = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        local_pos = event.position().toPoint()
        if self._resizing:
            self._performResize(event.globalPosition().toPoint())
            event.accept()
            return
        else:
            # update cursor shape near edges
            edge = self._getEdgeAtPos(local_pos)
            self._setCursorForEdge(edge)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._resizing = False
        self._resize_dir = None
        super().mouseReleaseEvent(event)

    def _performResize(self, global_pos: QPoint):
        if not self._resize_dir:
            return
        diff = global_pos - self._mouse_press_pos
        geo = QRect(self._mouse_press_geo)

        if "left" in self._resize_dir:
            new_x = geo.x() + diff.x()
            new_w = geo.width() - diff.x()
            if new_w >= self.minimumWidth():
                geo.setLeft(new_x)
            else:
                geo.setLeft(geo.right() - self.minimumWidth() + 1)

        if "right" in self._resize_dir:
            new_w = geo.width() + diff.x()
            if new_w >= self.minimumWidth():
                geo.setWidth(new_w)
            else:
                geo.setWidth(self.minimumWidth())

        if "top" in self._resize_dir:
            new_y = geo.y() + diff.y()
            new_h = geo.height() - diff.y()
            if new_h >= self.minimumHeight():
                geo.setTop(new_y)
            else:
                geo.setTop(geo.bottom() - self.minimumHeight() + 1)

        if "bottom" in self._resize_dir:
            new_h = geo.height() + diff.y()
            if new_h >= self.minimumHeight():
                geo.setHeight(new_h)
            else:
                geo.setHeight(self.minimumHeight())

        self.setGeometry(geo)

    # Make sure the titlebar buttons reflect maximize state
    def showMaximized(self):
        super().showMaximized()
        self.titlebar.btn_max.setText("❐")

    def showNormal(self):
        super().showNormal()
        self.titlebar.btn_max.setText("⬜")

    # Ensure keyboard shortcuts / focus remain usable
    def keyPressEvent(self, event):
        # Alt+F4 close, Alt+Space show menu, etc.
        if event.key() == Qt.Key_Space and event.modifiers() & Qt.AltModifier:
            # show system menu near titlebar
            self.titlebar._showSystemMenu(QPoint(0, 0))
        super().keyPressEvent(event)


# def main():
#     import sys
#
#     app = QApplication(sys.argv)
#     # High DPI scaling
#     QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
#     QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
#
#     win = FramelessWindow()
#     win.resize(900, 520)
#     win.show()
#     sys.exit(app.exec())
#
#
# if __name__ == "__main__":
#     main()
