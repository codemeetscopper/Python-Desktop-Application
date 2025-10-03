from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QFileDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QGridLayout, QLineEdit, QPushButton, QSizePolicy, QGroupBox, QFormLayout, QScrollArea
)
from PySide6.QtGui import QColor, QPainter

from common.appearance.stylemanager import StyleManager
from common.configuration.parser import ConfigurationManager
from common.tester.tester import Ui_TesterWindow

class ColourSwatch(QWidget):
    def __init__(self, color: QColor, tag: str, value: str, parent=None):
        super().__init__(parent)
        self._color = color
        self._tag = tag
        self._value = value
        self.setFixedSize(160, 40)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self._color)
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())
        painter.setPen(Qt.black if self._color.lightness() > 128 else Qt.white)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        text = f"{self._tag}: {self._value}"
        painter.drawText(self.rect(), Qt.AlignCenter, text)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_TesterWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Common Tester")

        file_path, _ = QFileDialog.getOpenFileName(self, "Select config file.", r"../../config")
        self._config = ConfigurationManager(file_path)
        self.combos = {}
        self.lineedits = {}

        self._init_ui()
        self.reload_palette()

    def _init_ui(self):
        container = QWidget()
        self.layout = QHBoxLayout(container)
        self.setCentralWidget(container)
        self.container = container

    def reload_palette(self):
        # Clear layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

        accent = self._config.get_value('accent')
        support = self._config.get_value('support')
        neutral = self._config.get_value('neutral')
        theme = self._config.get_value('theme')

        # --- Settings Section ---
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout()
        self.combos = {}
        self.lineedits = {}

        # User settings
        user_settings = self._config.data.configuration.user
        for key, setting in user_settings.items():
            label = QLabel(setting.name)
            if setting.type == "dropdown":
                combo = QComboBox()
                combo.addItems(setting.values)
                combo.setCurrentText(setting.value)
                combo.currentTextChanged.connect(lambda val, k=key: self.on_setting_changed(k, val))
                settings_layout.addRow(label, combo)
                self.combos[key] = combo
            elif setting.type == "text":
                lineedit = QLineEdit()
                lineedit.setText(str(setting.value))
                lineedit.editingFinished.connect(lambda k=key, le=lineedit: self.on_text_setting_changed(k, le))
                settings_layout.addRow(label, lineedit)
                self.lineedits[key] = lineedit
            else:
                lineedit = QLineEdit()
                lineedit.setText(str(setting.value))
                lineedit.setReadOnly(True)
                settings_layout.addRow(label, lineedit)

        # Static settings (always as read-only textboxes)
        static_settings = self._config.data.configuration.static
        for key, value in static_settings.items():
            label = QLabel(key)
            lineedit = QLineEdit()
            lineedit.setText(str(value))
            lineedit.setReadOnly(True)
            settings_layout.addRow(label, lineedit)

        settings_group.setLayout(settings_layout)
        self.layout.addWidget(settings_group)

        # --- Palette Section ---
        StyleManager.initialise(accent.value, support.value, neutral.value, theme=theme.value)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(12, 12, 12, 12)

        palette_group = QGroupBox("Palette")
        grid = QGridLayout()
        grid.setSpacing(12)
        keys = sorted(StyleManager._colours.keys())
        cols = 3
        for idx, key in enumerate(keys):
            color = StyleManager.get_colour(key, to_str=False)
            hexval = StyleManager.get_colour(key, to_str=True)
            swatch = ColourSwatch(color, key, hexval)
            row, col = divmod(idx, cols)
            grid.addWidget(swatch, row, col)
        palette_group.setLayout(grid)
        self.layout.addWidget(palette_group)

        self.setPalette(StyleManager.get_palette())

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def on_setting_changed(self, key, value):
        self._config.set_value(key, value)
        self.reload_palette()

    def on_text_setting_changed(self, key, lineedit):
        value = lineedit.text()
        self._config.set_value(key, value)
        self.reload_palette()

def run():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == "__main__":
    run()
