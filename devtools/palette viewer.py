import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QSizePolicy
)
from PySide6.QtGui import QColor
from common.appearance.stylemanager import StyleManager
from common.configuration.parser import ConfigurationManager


class ColourSwatch(QWidget):
    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(40, 24)

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter
        painter = QPainter(self)
        painter.setBrush(self._color)
        painter.setPen(self._color)
        painter.drawRect(self.rect())

class ColourViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StyleManager Colour Keys")
        self.resize(400, 600)

        # Initialize StyleManager with some sample colors
        config = ConfigurationManager(r"D:\Development\Python\Python-Desktop-Application\config\configuration.json")
        accent = config.get_value('accent')
        support = config.get_value('support')
        neutral = config.get_value('neutral')
        theme = config.get_value('theme')

        StyleManager.initialise(accent.value, support.value, neutral.value, theme=theme.value)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        for key in sorted(StyleManager._colours.keys()):
            color = StyleManager.get_colour(key, to_str=False)
            hexval = StyleManager.get_colour(key, to_str=True)
            row = QHBoxLayout()
            row.setSpacing(16)
            swatch = ColourSwatch(color)
            label = QLabel(key)
            label.setMinimumWidth(100)
            hex_label = QLabel(hexval)
            row.addWidget(swatch)
            row.addWidget(label)
            row.addWidget(hex_label)
            row.addStretch()
            layout.addLayout(row)

        container.setLayout(layout)
        scroll.setWidget(container)
        self.setCentralWidget(scroll)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ColourViewer()
    win.show()
    sys.exit(app.exec())
