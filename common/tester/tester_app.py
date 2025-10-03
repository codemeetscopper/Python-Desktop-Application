import os
import shutil
import json
import logging
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QFileDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QGridLayout, QLineEdit, QPushButton, QSizePolicy, QGroupBox, QFormLayout, QScrollArea,
    QSpinBox, QTextEdit, QSplitter, QFrame
)
from PySide6.QtGui import QColor, QPainter, QIcon

from common.appearance.stylemanager import StyleManager
from common.configuration.parser import ConfigurationManager, SettingItem
from common.tester.tester import Ui_TesterWindow
from common.appearance.fontmanager import FontManager
from common.appearance.iconmanager import IconManager
from common.logger import Logger
from common.tcpinterface.backendserver import BackendServer
from common.tcpinterface.backendclient import BackendClient
from common.tcpinterface.aes import AESCipher

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

        # Main layout setup
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(self.ui.main_tw)
        self.setCentralWidget(main_splitter)

        file_path, _ = QFileDialog.getOpenFileName(self, "Select config file.", r"../../config")
        self._config = ConfigurationManager(file_path)
        self.combos = {}
        self.lineedits = {}
        self._font_manager = FontManager()
        self._logger = Logger()
        self._server = None
        self._client = None
        self._aes_cipher = None

        self.ui.menubar.setVisible(False)

        self.setup_tabs()
        self.setup_logger_ui(main_splitter) # Pass splitter to add logger
        main_splitter.setSizes([self.height() // 2, self.height() // 2]) # Set 1:1 ratio
        self.reload_ui()

    def setup_tabs(self):
        # Settings Tab
        self.settings_tab = QWidget()
        self.settings_layout = QFormLayout(self.settings_tab)
        self.ui.main_tw.addTab(self.settings_tab, "Settings")

        # Palette Tab
        self.palette_tab = QWidget()
        self.palette_layout = QGridLayout(self.palette_tab)
        self.palette_layout.setSpacing(12)
        self.ui.main_tw.addTab(self.palette_tab, "Palette")

        # Font Manager Tab
        self.font_tab = QWidget()
        self.font_layout = QVBoxLayout(self.font_tab)
        self.ui.main_tw.addTab(self.font_tab, "Fonts")
        self.setup_font_tab()

        # Icon Manager Tab
        self.icon_tab = QWidget()
        self.icon_layout = QVBoxLayout(self.icon_tab)
        self.ui.main_tw.addTab(self.icon_tab, "Icons")
        self.setup_icon_tab()

        # Logger Tab is removed from here

        # TCP Server Tab
        self.server_tab = QWidget()
        self.server_layout = QFormLayout(self.server_tab)
        self.ui.main_tw.addTab(self.server_tab, "TCP Server")
        self.setup_tcp_server_tab()

        # TCP Client Tab
        self.client_tab = QWidget()
        self.client_layout = QFormLayout(self.client_tab)
        self.ui.main_tw.addTab(self.client_tab, "TCP Client")
        self.setup_tcp_client_tab()

        # AES Tab
        self.aes_tab = QWidget()
        self.aes_layout = QVBoxLayout(self.aes_tab)
        self.ui.main_tw.addTab(self.aes_tab, "AES Cipher")
        self.setup_aes_tab()

    def setup_logger_ui(self, parent_splitter):
        logger_group = QGroupBox("Logs")
        logger_layout = QVBoxLayout(logger_group)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        logger_layout.addWidget(self.log_display)

        controls_layout = QHBoxLayout()
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        level_combo = QComboBox()
        level_combo.addItems(levels)
        level_combo.setCurrentText(logging.getLevelName(self._logger.level))
        level_combo.currentTextChanged.connect(self.on_log_level_changed)
        controls_layout.addWidget(QLabel("Log Level:"))
        controls_layout.addWidget(level_combo)
        controls_layout.addStretch()

        for level in levels:
            btn = QPushButton(level.capitalize())
            btn.clicked.connect(lambda checked=False, l=level.lower(): getattr(self._logger, l)(f"This is a {l} message."))
            controls_layout.addWidget(btn)

        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_logs)
        controls_layout.addWidget(export_btn)
        logger_layout.addLayout(controls_layout)

        parent_splitter.addWidget(logger_group)
        self._logger.log_updated.connect(lambda msg: self.log_display.append(msg))

    def on_log_level_changed(self, level_str: str):
        level = logging.getLevelName(level_str)
        self._logger.set_level(level)
        self._logger.info(f"Log level changed to {level_str}")

    def export_logs(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Log File", "", "Log Files (*.log)")
        if path:
            self._logger.export_to_file(path)

    def setup_tcp_server_tab(self):
        self.server_host_input = QLineEdit("127.0.0.1")
        self.server_port_input = QLineEdit("5000")
        self.server_key_input = QLineEdit("a_secure_32_byte_secret_key_!!!!")
        self.server_status_label = QLabel("Status: Stopped")
        self.start_server_btn = QPushButton("Start Server")
        self.stop_server_btn = QPushButton("Stop Server")
        self.stop_server_btn.setEnabled(False)

        self.start_server_btn.clicked.connect(self.start_server)
        self.stop_server_btn.clicked.connect(self.stop_server)

        self.server_layout.addRow("Host:", self.server_host_input)
        self.server_layout.addRow("Port:", self.server_port_input)
        self.server_layout.addRow("Secret Key:", self.server_key_input)
        self.server_layout.addRow(self.start_server_btn, self.stop_server_btn)
        self.server_layout.addRow(self.server_status_label)

    def start_server(self):
        host = self.server_host_input.text()
        port = int(self.server_port_input.text())
        key = self.server_key_input.text().encode('utf-8')
        try:
            self._server = BackendServer(host, port, key)
            self._server.register_function(lambda x, y: x + y, "add")
            self._server.register_function(lambda: "pong", "ping")
            self._server.start()
            self.server_status_label.setText("Status: Running")
            self.start_server_btn.setEnabled(False)
            self.stop_server_btn.setEnabled(True)
        except Exception as e:
            self.server_status_label.setText(f"Status: Error - {e}")

    def stop_server(self):
        if self._server:
            self._server.stop()
            self._server = None
        self.server_status_label.setText("Status: Stopped")
        self.start_server_btn.setEnabled(True)
        self.stop_server_btn.setEnabled(False)

    def setup_tcp_client_tab(self):
        self.client_host_input = QLineEdit("127.0.0.1")
        self.client_port_input = QLineEdit("5000")
        self.client_key_input = QLineEdit("a_secure_32_byte_secret_key_!!!!")
        self.client_func_input = QLineEdit("ping")
        self.client_args_input = QLineEdit("[]")
        self.client_kwargs_input = QLineEdit("{}")
        self.call_btn = QPushButton("Call Function")
        self.client_response_display = QTextEdit()
        self.client_response_display.setReadOnly(True)

        self.call_btn.clicked.connect(self.call_server_function)

        self.client_layout.addRow("Host:", self.client_host_input)
        self.client_layout.addRow("Port:", self.client_port_input)
        self.client_layout.addRow("Secret Key:", self.client_key_input)
        self.client_layout.addRow("Function:", self.client_func_input)
        self.client_layout.addRow("Args (JSON):", self.client_args_input)
        self.client_layout.addRow("Kwargs (JSON):", self.client_kwargs_input)
        self.client_layout.addRow(self.call_btn)
        self.client_layout.addRow(self.client_response_display)

    def call_server_function(self):
        host = self.client_host_input.text()
        port = int(self.client_port_input.text())
        key = self.client_key_input.text().encode('utf-8')
        func = self.client_func_input.text()
        try:
            args = json.loads(self.client_args_input.text())
            kwargs = json.loads(self.client_kwargs_input.text())
            client = BackendClient(host, port, secret_key=key)
            response = client.call(func, *args, **kwargs)
            self.client_response_display.setText(json.dumps(response, indent=2))
        except Exception as e:
            self.client_response_display.setText(f"Error: {e}")

    def setup_aes_tab(self):
        self.aes_key_input = QLineEdit("a_secure_32_byte_secret_key_!!!!")
        self.aes_plaintext_input = QTextEdit()
        self.aes_ciphertext_input = QTextEdit()
        encrypt_btn = QPushButton("Encrypt ↓")
        decrypt_btn = QPushButton("↑ Decrypt")

        encrypt_btn.clicked.connect(self.encrypt_aes)
        decrypt_btn.clicked.connect(self.decrypt_aes)

        key_layout = QFormLayout()
        key_layout.addRow("Secret Key (32 bytes):", self.aes_key_input)
        self.aes_layout.addLayout(key_layout)

        self.aes_layout.addWidget(QLabel("Plaintext:"))
        self.aes_layout.addWidget(self.aes_plaintext_input)

        button_layout = QHBoxLayout()
        button_layout.addWidget(encrypt_btn)
        button_layout.addWidget(decrypt_btn)
        self.aes_layout.addLayout(button_layout)

        self.aes_layout.addWidget(QLabel("Ciphertext:"))
        self.aes_layout.addWidget(self.aes_ciphertext_input)

    def encrypt_aes(self):
        try:
            key = self.aes_key_input.text().encode('utf-8')
            self._aes_cipher = AESCipher(key)
            plaintext = self.aes_plaintext_input.toPlainText()
            encrypted = self._aes_cipher.encrypt_string(plaintext)
            self.aes_ciphertext_input.setText(encrypted)
        except Exception as e:
            self.aes_ciphertext_input.setText(f"Encryption Error: {e}")

    def decrypt_aes(self):
        try:
            key = self.aes_key_input.text().encode('utf-8')
            self._aes_cipher = AESCipher(key)
            ciphertext = self.aes_ciphertext_input.toPlainText()
            decrypted = self._aes_cipher.decrypt_string(ciphertext)
            self.aes_plaintext_input.setText(decrypted)
        except Exception as e:
            self.aes_plaintext_input.setText(f"Decryption Error: {e}")

    def set_application_font(self, tag: str):
        """Sets the application-wide font."""
        try:
            font = self._font_manager.get_font(tag)
            app = QApplication.instance()
            app.setFont(font)
            # Re-apply palette and style to force font update across all widgets
            app.setPalette(StyleManager.get_palette())
            self._logger.info(f"Application font set to '{tag}' with size {font.pointSize()}.")
        except (RuntimeError, StopIteration):
            self._logger.error(f"Could not set application font. Tag '{tag}' not found.")

    def on_font_size_changed(self, tag, size, label):
        self._font_manager.set_font_size(tag, size)
        font = self._font_manager.get_font(tag)
        label.setFont(font)

    def setup_font_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.font_display_widget = QWidget()
        self.font_display_layout = QVBoxLayout(self.font_display_widget)
        scroll.setWidget(self.font_display_widget)
        self.font_layout.addWidget(scroll)
        self.preload_and_display_fonts()

    def preload_and_display_fonts(self):
        self.clear_layout(self.font_display_layout)
        font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'fonts'))
        if not os.path.isdir(font_path):
            self.font_display_layout.addWidget(QLabel("Font directory not found."))
            return

        for filename in os.listdir(font_path):
            if filename.lower().endswith(('.ttf', '.otf')):
                full_path = os.path.join(font_path, filename)
                tag = os.path.splitext(filename)[0]
                try:
                    self._font_manager.load_font(full_path, tag=tag, size=12)
                except (RuntimeError, FileNotFoundError) as e:
                    print(f"Could not load font {filename}: {e}")
                    continue

        for tag, font_info in self._font_manager.get_font_map().items():
            # Top row for controls
            top_row_layout = QHBoxLayout()
            top_row_layout.addWidget(QLabel(f"<b>{tag}</b>"))
            top_row_layout.addStretch()

            size_spinbox = QSpinBox()
            size_spinbox.setRange(6, 72)
            size_spinbox.setValue(font_info['size'])
            top_row_layout.addWidget(QLabel("Size:"))
            top_row_layout.addWidget(size_spinbox)

            set_app_font_btn = QPushButton("Set to Application")
            top_row_layout.addWidget(set_app_font_btn)

            # Bottom row for preview
            preview_label = QLabel("The quick brown fox jumps over the lazy dog.")
            font = self._font_manager.get_font(tag)
            preview_label.setFont(font)

            # Connections
            size_spinbox.valueChanged.connect(
                lambda size, t=tag, lbl=preview_label: self.on_font_size_changed(t, size, lbl)
            )
            set_app_font_btn.clicked.connect(lambda checked=False, t=tag: self.set_application_font(t))

            # Main layout for this font entry
            entry_layout = QVBoxLayout()
            entry_layout.addLayout(top_row_layout)
            entry_layout.addWidget(preview_label)

            # # Add a separator
            # separator = QFrame()
            # separator.setFrameShape(QFrame.HLine)
            # separator.setFrameShadow(QFrame.Sunken)
            # entry_layout.addWidget(separator)

            self.font_display_layout.addLayout(entry_layout)

    def setup_icon_tab(self):
        # Set path relative to this script's location
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'images'))
        IconManager.set_images_path(icon_path)

        # --- Controls ---
        controls_layout = QFormLayout()
        self.icon_color_combo = QComboBox()
        self.icon_size_input = QSpinBox()
        self.icon_size_input.setRange(8, 128)
        self.icon_size_input.setValue(32)
        load_icon_btn = QPushButton("Load New Icon(s)")
        load_icon_btn.clicked.connect(self.load_new_icons)

        self.icon_color_combo.currentTextChanged.connect(self.update_icon_display)
        self.icon_size_input.valueChanged.connect(self.update_icon_display)

        controls_layout.addRow("Color:", self.icon_color_combo)
        controls_layout.addRow("Size:", self.icon_size_input)
        controls_layout.addRow(load_icon_btn)
        self.icon_layout.addLayout(controls_layout)

        # --- Icon Display ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.icon_grid_widget = QWidget()
        self.icon_grid_layout = QGridLayout(self.icon_grid_widget)
        scroll.setWidget(self.icon_grid_widget)
        self.icon_layout.addWidget(scroll)
        self.update_icon_display()

    def load_new_icons(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select SVG Icon(s)", "", "SVG Files (*.svg)")
        if not files:
            return

        dest_path = IconManager.get_images_path()
        for file_path in files:
            try:
                shutil.copy(file_path, dest_path)
            except Exception as e:
                print(f"Failed to copy {file_path} to {dest_path}: {e}")

        IconManager.clear_cache()
        self.update_icon_display()

    def update_icon_display(self):
        self.clear_layout(self.icon_grid_layout)
        color_key = self.icon_color_combo.currentText()

        if not color_key:
            return

        color = StyleManager.get_colour(color_key)
        size = self.icon_size_input.value()
        cols = 5

        icon_names = IconManager.list_icons()
        if not icon_names:
            self.icon_grid_layout.addWidget(QLabel("No icons found in the specified path."), 0, 0)
            return

        for idx, name in enumerate(sorted(icon_names)):
            pixmap = IconManager.get_pixmap(name, color, size)
            icon_label = QLabel()
            icon_label.setPixmap(pixmap)
            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignCenter)

            cell_widget = QWidget()
            cell_layout = QVBoxLayout(cell_widget)
            cell_layout.addWidget(icon_label, alignment=Qt.AlignCenter)
            cell_layout.addWidget(name_label)

            row, col = divmod(idx, cols)
            self.icon_grid_layout.addWidget(cell_widget, row, col)

    def reload_ui(self):
        # Clear layouts
        self.clear_layout(self.settings_layout)
        self.clear_layout(self.palette_layout)

        accent = self._config.get_value('accent')
        support = self._config.get_value('support')
        neutral = self._config.get_value('neutral')
        theme = self._config.get_value('theme')

        # --- Populate Settings Tab ---
        self.combos = {}
        self.lineedits = {}
        theme_keys = ['accent', 'support', 'neutral', 'theme']

        # User settings
        user_settings = self._config.data.configuration.user
        for key, setting in user_settings.items():
            if key in theme_keys:
                continue  # Skip theme settings, they are on the palette tab

            label = QLabel(setting.name)
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked=False, k=key: self.delete_setting(k))

            if setting.type == "dropdown":
                combo = QComboBox()
                combo.addItems(setting.values)
                combo.setCurrentText(setting.value)
                combo.currentTextChanged.connect(lambda val, k=key: self.on_setting_changed(k, val))

                row = QHBoxLayout()
                row.addWidget(combo)
                row.addWidget(delete_btn)
                self.settings_layout.addRow(label, row)
                self.combos[key] = combo
            elif setting.type == "text":
                lineedit = QLineEdit()
                lineedit.setText(str(setting.value))
                lineedit.editingFinished.connect(lambda k=key, le=lineedit: self.on_text_setting_changed(k, le))

                row = QHBoxLayout()
                row.addWidget(lineedit)
                row.addWidget(delete_btn)
                self.settings_layout.addRow(label, row)
                self.lineedits[key] = lineedit
            else:
                lineedit = QLineEdit()
                lineedit.setText(str(setting.value))
                lineedit.setReadOnly(True)
                self.settings_layout.addRow(label, lineedit)

        # Static settings (always as read-only textboxes)
        static_settings = self._config.data.configuration.static
        for key, value in static_settings.items():
            label = QLabel(key)
            lineedit = QLineEdit()
            lineedit.setText(str(value))
            lineedit.setReadOnly(True)
            self.settings_layout.addRow(label, lineedit)

        # --- Add New Setting Form ---
        new_setting_group = QGroupBox("Add New User Setting")
        new_setting_layout = QFormLayout(new_setting_group)
        self.new_setting_key = QLineEdit()
        self.new_setting_name = QLineEdit()
        self.new_setting_value = QLineEdit()
        self.new_setting_type = QComboBox()
        self.new_setting_type.addItems(["text", "dropdown"])
        self.new_setting_values = QLineEdit()
        self.new_setting_desc = QLineEdit()
        self.new_setting_group = QLineEdit()
        add_button = QPushButton("Add Setting")
        add_button.clicked.connect(self.add_new_setting)

        new_setting_layout.addRow("Key*:", self.new_setting_key)
        new_setting_layout.addRow("Name:", self.new_setting_name)
        new_setting_layout.addRow("Type:", self.new_setting_type)
        new_setting_layout.addRow("Default Value:", self.new_setting_value)
        new_setting_layout.addRow("Values (CSV for dropdown):", self.new_setting_values)
        new_setting_layout.addRow("Description:", self.new_setting_desc)
        new_setting_layout.addRow("Group:", self.new_setting_group)
        new_setting_layout.addRow(add_button)

        # Find the layout of the settings tab and add the groupbox
        self.settings_tab.layout().addWidget(new_setting_group)

        # --- Populate Palette Tab ---
        # Theme settings dropdowns
        theme_settings_layout = QFormLayout()
        for key in theme_keys:
            setting = user_settings[key]
            combo = QComboBox()
            combo.addItems(setting.values)
            combo.setCurrentText(setting.value)
            combo.currentTextChanged.connect(lambda val, k=key: self.on_setting_changed(k, val))
            theme_settings_layout.addRow(QLabel(setting.name), combo)
            self.combos[key] = combo

        palette_container = QWidget()
        palette_main_layout = QVBoxLayout(palette_container)
        palette_main_layout.addLayout(theme_settings_layout)

        # Palette grid
        StyleManager.initialise(accent, support, neutral, theme=theme)

        palette_grid = QGridLayout()
        palette_grid.setSpacing(12)
        keys = sorted(StyleManager._colours.keys())
        cols = 3
        for idx, key in enumerate(keys):
            color = StyleManager.get_colour(key, to_str=False)
            hexval = StyleManager.get_colour(key, to_str=True)
            swatch = ColourSwatch(color, key, hexval)
            row, col = divmod(idx, cols)
            palette_grid.addWidget(swatch, row, col)
        palette_main_layout.addLayout(palette_grid)
        self.palette_layout.addWidget(palette_container)


        # --- Populate Icon Color Dropdown ---
        self.icon_color_combo.blockSignals(True)
        self.icon_color_combo.clear()
        color_keys = sorted(StyleManager._colours.keys())
        self.icon_color_combo.addItems(color_keys)
        if 'fg' in color_keys:
            self.icon_color_combo.setCurrentText('fg')
        self.icon_color_combo.blockSignals(False)

        self.setPalette(StyleManager.get_palette())
        self.update_icon_display()

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
        self.reload_ui()

    def on_text_setting_changed(self, key, lineedit):
        value = lineedit.text()
        self._config.set_value(key, value)
        self.reload_ui()

    def add_new_setting(self):
        key = self.new_setting_key.text()
        if not key:
            self._logger.error("Setting key cannot be empty.")
            return

        values = [v.strip() for v in self.new_setting_values.text().split(',') if v.strip()]

        new_item = SettingItem(
            name=self.new_setting_name.text(),
            value=self.new_setting_value.text(),
            values=values,
            description=self.new_setting_desc.text(),
            type=self.new_setting_type.currentText(),
            accessibility="user",
            group=self.new_setting_group.text(),
            icon=""
        )

        try:
            self._config.add_user_setting(key, new_item)
            self._logger.info(f"Setting '{key}' added successfully.")
            # Clear input fields
            self.new_setting_key.clear()
            self.new_setting_name.clear()
            self.new_setting_value.clear()
            self.new_setting_values.clear()
            self.new_setting_desc.clear()
            self.new_setting_group.clear()
            self.reload_ui()
        except Exception as e:
            self._logger.error(f"Failed to add setting '{key}': {e}")

    def delete_setting(self, key: str):
        try:
            self._config.delete_user_setting(key)
            self._logger.info(f"Setting '{key}' deleted successfully.")
            self.reload_ui()
        except Exception as e:
            self._logger.error(f"Failed to delete setting '{key}': {e}")

def run():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == "__main__":
    run()
