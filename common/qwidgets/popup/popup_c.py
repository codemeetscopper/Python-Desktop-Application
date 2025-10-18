from typing import Optional

from PySide6.QtCore import Qt, QEventLoop, QSize
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QIcon

from common import AppCntxt
from common.qwidgets.popup.popup import Ui_Popup


class Popup(QWidget):
    """
    Minimal popup widget with a single static API:
        Popup.show_popup(header, message, mtype='info', parent=None, ok_text='OK', cancel_text='Cancel') -> bool

    - Returns True if user clicks OK/Yes, False on Cancel/No or close.
    - mtype controls icon and cancel button visibility.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.ui = Ui_Popup()
        self.ui.setupUi(self)

        # Window look & modality
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(600, 300)

        # App-wide style and font
        self.setPalette(AppCntxt.styler.get_palette())
        self.setFont(AppCntxt.font.get_font('pc'))
        self.ui.header.setFont(AppCntxt.font.get_font('h2'))
        self.ui.header.setStyleSheet(f"color: {AppCntxt.styler.get_colour('accent')}")
        self.ui.message.setWordWrap(True)

        # Internal result
        self._result: bool = False
        self._loop: Optional[QEventLoop] = None

        # Button handlers
        self.ui.okbtn.clicked.connect(self._on_ok)
        self.ui.cancelbtn.clicked.connect(self._on_cancel)

    # -------- Public single API (static) --------
    @staticmethod
    def show_popup(
        header: str,
        message: str,
        mtype: str = "info",
        *,
        parent: Optional[QWidget] = None,
        ok_text: str = "OK",
        cancel_text: str = "Cancel",
    ) -> bool:
        """
        Show a popup and block until user responds.
        mtype: 'info' | 'warning' | 'error' | 'question' | 'success'
        Returns True for OK/Yes, False for Cancel/No or close.
        """
        popup = Popup(parent)
        popup._set_content(header, message, mtype, ok_text, cancel_text)
        popup._center_on(parent or popup.window())

        popup._loop = QEventLoop(popup)
        popup.show()
        popup.raise_()
        popup.activateWindow()
        popup._loop.exec()
        return popup._result

    # -------- Internals --------
    def _set_content(self, header: str, message: str, mtype: str, ok_text: str, cancel_text: str) -> None:
        self.ui.header.setText(header or "")
        self.ui.message.setText(message or "")
        self.ui.okbtn.setText(ok_text or "OK")
        self.ui.cancelbtn.setText(cancel_text or "Cancel")

        mtype = (mtype or "info").strip().lower()
        self._set_icon_by_type(mtype)

        # Cancel visible for question/warning/error; hidden for info/success
        show_cancel = mtype in ("question", "warning", "error")
        self.ui.cancelbtn.setVisible(show_cancel)

        # Default focus on OK
        self.ui.okbtn.setDefault(True)
        self.ui.okbtn.setAutoDefault(True)
        self.ui.okbtn.setFocus()

    def _set_icon_by_type(self, mtype: str) -> None:
        style = self.style()
        if mtype == "warning":
            sp = AppCntxt.styler.get_pixmap('warning',
                                            AppCntxt.styler.get_colour('accent'),
                                            50)
        elif mtype == "error":
            sp = AppCntxt.styler.get_pixmap('error',
                                            AppCntxt.styler.get_colour('accent'),
                                            50)
        elif mtype == "question":
            sp = AppCntxt.styler.get_pixmap('question',
                                            AppCntxt.styler.get_colour('accent'),
                                            50)
        elif mtype == "success":
            sp = AppCntxt.styler.get_pixmap('success',
                                            AppCntxt.styler.get_colour('accent'),
                                            50)
        else:
            sp = AppCntxt.styler.get_pixmap('success',
                                            AppCntxt.styler.get_colour('accent'),
                                            50)
        icon = QIcon(sp)
        lbl_size = self.ui.icon.size()
        if not lbl_size.isValid() or lbl_size.width() == 0 or lbl_size.height() == 0:
            lbl_size = QSize(48, 48)

        dpr = max(self.devicePixelRatioF(), 1.0)
        pm = icon.pixmap(int(lbl_size.width() * dpr), int(lbl_size.height() * dpr))
        pm.setDevicePixelRatio(dpr)
        self.ui.icon.setPixmap(pm)

    def _center_on(self, widget: Optional[QWidget]) -> None:
        if widget is None:
            # Fallback to screen center
            self.move(self.screen().geometry().center() - self.rect().center())
            return
        geo = widget.frameGeometry()
        my_geo = self.frameGeometry()
        my_geo.moveCenter(geo.center())
        self.move(my_geo.topLeft())

    def _finish(self):
        if self._loop and self._loop.isRunning():
            self._loop.quit()
        self.close()

    def _on_ok(self):
        self._result = True
        self._finish()

    def _on_cancel(self):
        self._result = False
        self._finish()

    # Treat closing as Cancel
    def closeEvent(self, event):
        if self._loop and self._loop.isRunning():
            self._result = False
            self._loop.quit()
        super().closeEvent(event)

    # Keyboard shortcuts: Enter -> OK, Esc -> Cancel
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._on_ok()
            return
        if event.key() == Qt.Key.Key_Escape:
            self._on_cancel()
            return
        super().keyPressEvent(event)
