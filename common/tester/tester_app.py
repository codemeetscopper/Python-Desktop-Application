import hashlib
import os
import shutil
import json
import logging
import time
import asyncio
import re
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QFileDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QGridLayout, QLineEdit, QPushButton, QGroupBox, QFormLayout, QScrollArea,
    QSpinBox, QTextEdit, QSplitter, QFrame, QColorDialog, QTabWidget, QProgressBar
)
from PySide6.QtGui import QColor, QPainter, QPixmap, QImage

from common import threadmanager, AppData, initialise_context
from common.appearance.stylemanager import StyleManager
from common.configuration.parser import ConfigurationManager, SettingItem
from common.qwidgets.titlebar import CustomTitleBar
from common.tester.tester import Ui_TesterWindow
from common.appearance.fontmanager import FontManager
from common.appearance.iconmanager import IconManager
from common.logger import Logger
from common.tcpinterface.backendserver import BackendServer
from common.tcpinterface.backendclient import BackendClient
from common.tcpinterface.aes import AESCipher
from common import AppCntxt
from common.tester.qss_editor import QssEditorWidget
from common.appearance.qssmanager import QSSManager



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
    # Signal to update UI safely from other threads
    update_status_signal = Signal(QLabel, str)

    def __init__(self):
        super().__init__()
        self.ui = Ui_TesterWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Tester Application")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.Window)

        file_path, _ = QFileDialog.getOpenFileName(self, "Select config file.", r"../../config")
        self._config = ConfigurationManager(file_path)
        # self._initialise_context()
        initialise_context()

        # Load paths from config and make them absolute
        project_root = os.path.abspath(os.path.join(os.path.dirname(file_path), '..'))
        icon_path_rel = self._config.get_value('icon_path')
        self.font_path_abs = os.path.join(project_root, self._config.get_value('font_path'))
        icon_path_abs = os.path.join(project_root, icon_path_rel)

        IconManager.set_images_path(icon_path_abs)
        IconManager.list_icons()

        main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.titlebar = CustomTitleBar(self)
        main_splitter.addWidget(self.titlebar)


        # Main layout setup
        sub_splitter = QSplitter(Qt.Orientation.Vertical)
        # self.ui.main_tw.setMinimumWidth(800)
        sub_splitter.addWidget(self.ui.main_tw)
        main_splitter.addWidget(sub_splitter)
        self.setCentralWidget(main_splitter)


        self.combos = {}
        self.lineedits = {}
        self._font_manager = FontManager()
        self._logger = Logger()
        self._server = None
        self._client = None
        self._aes_cipher = None

        # self.ui.menubar.setVisible(False)

        # --- Icon Tab State ---
        self._icon_label_map: dict[str, QLabel] = {}
        self._icon_notifier_connected = False
        self._loading_total = 0
        self._loaded_count = 0
        self._icon_load_generation = 0  # Generation counter to discard old async results

        self.setup_tabs()
        self.setup_logger_ui(sub_splitter) # Pass splitter to add logger
        # main_splitter.setSizes([self.height() // 2, self.height() // 2]) # Set 1:1 ratio
        self.reload_ui()
        self.setMinimumWidth(900)
        self.set_application_font('pc')


        # self.ui.setupUi(self)
        # self.ui.verticalLayout.layout().insertWidget(0, self.titlebar)
        self.update_status_signal.connect(self.update_label_text)

    def update_label_text(self, label: QLabel, text: str):
        """Slot to safely update a QLabel's text from any thread."""
        label.setText(text)

    def _initialise_context(self):
        AppCntxt.logger = Logger()
        AppCntxt.threader = threadmanager.get_instance()

        AppCntxt.data = AppData()

        AppCntxt.threader.start()
        AppCntxt.settings = self._config

        ip = AppCntxt.settings.get_value('sdk_ip_address')
        port = AppCntxt.settings.get_value('sdk_tcp_port')
        timeout = AppCntxt.settings.get_value('sdk_tcp_timeout')
        # key = AppCntxt.settings.get_value('sdk_aes_key')
        key = hashlib.sha256(b"sample key").digest()
        AppCntxt.backend = BackendClient(ip, port, timeout, secret_key=key)

        AppCntxt.styler = StyleManager()
        accent = AppCntxt.settings.get_value('accent')
        support = AppCntxt.settings.get_value('support')
        neutral = AppCntxt.settings.get_value('neutral')
        theme = AppCntxt.settings.get_value('theme')
        AppCntxt.styler.initialise(accent, support, neutral, theme)

        AppCntxt.font = FontManager()
        AppCntxt.font.load_font(r"../../resources/fonts/RobotoCondensed-VariableFont_wght.ttf", "h1", 18)
        AppCntxt.font.load_font(r"../../resources/fonts/RobotoCondensed-VariableFont_wght.ttf", "h2", 14)
        AppCntxt.font.load_font(r"../../resources/fonts/Roboto-VariableFont_wdth,wght.ttf", "p", 11)
        AppCntxt.font.load_font(r"../../resources/fonts/RobotoCondensed-VariableFont_wght.ttf", "pc", 10)
        AppCntxt.font.load_font(r"../../resources/fonts/Inconsolata-VariableFont_wdth,wght.ttf", "log", 11)
        QApplication.processEvents()

    def setup_tabs(self):
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

        # QSS Editor Tab
        self.qss_tab = QWidget()
        self.qss_layout = QVBoxLayout(self.qss_tab)
        self.ui.main_tw.addTab(self.qss_tab, "QSS Editor")
        self.setup_qss_editor_tab()

        # Thread Manager Tab
        self.thread_tab = QWidget()
        self.thread_layout = QVBoxLayout(self.thread_tab)
        self.ui.main_tw.addTab(self.thread_tab, "Threading")
        self.setup_thread_manager_tab()

        # Settings Tab
        self.settings_tab = QWidget()
        # The main layout for the settings tab will be a QVBoxLayout to hold the new tab widget
        settings_main_layout = QVBoxLayout(self.settings_tab)
        settings_main_layout.setContentsMargins(0, 0, 0, 0)
        self.settings_tab_widget = QTabWidget()
        settings_main_layout.addWidget(self.settings_tab_widget)
        self.ui.main_tw.addTab(self.settings_tab, "Settings")

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

        # Data/Signals Tab
        self.data_tab = QWidget()
        self.data_layout = QVBoxLayout(self.data_tab)
        self.ui.main_tw.addTab(self.data_tab, "Data/Signals")
        self.setup_data_tab()



    def setup_logger_ui(self, parent_splitter):
        logger_group = QGroupBox("Logs")
        logger_layout = QVBoxLayout(logger_group)

        self.log_display = QTextEdit()
        self.log_display.setFont(self._font_manager.get_font('log'))
        # self.log_display.setMaximumWidth(600)
        # self.log_display.setReadOnly(True)
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
            btn.clicked.connect(lambda checked=False, l=level: getattr(self._logger, l)(f"This is a {l} message."))
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

    def setup_qss_editor_tab(self):
        """Sets up the UI for the QSS stylesheet editor tab."""
        # Remove the old inline editor UI and embed the dedicated widget
        # description kept for users who expect guidance
        description = QLabel(
            "Edit the QSS below. Use color keys like <accent>, <bg-l1>, etc. "
            "These will be replaced with colors from the current palette."
        )
        description.setWordWrap(True)
        self.qss_layout.addWidget(description)

        # use the new QssEditorWidget
        self.qss_widget = QssEditorWidget(parent=self.qss_tab)
        self.qss_layout.addWidget(self.qss_widget)

        # no local apply button here — the widget exposes apply buttons
        # ensure the tester app can still call apply_qss_style()
        # --- Pre-load default QSS is handled inside QssEditorWidget

    def apply_qss_style(self):
        """Applies the QSS from the editor to the application (delegates to QssEditorWidget)."""
        try:
            if hasattr(self, "qss_widget") and self.qss_widget:
                self.qss_widget.apply_qss(to_application=True)
            else:
                # fallback: if older inline editor exists (rare), process it
                raw_qss = getattr(self, "qss_editor", QTextEdit()).toPlainText()
                processed = QSSManager.process(raw_qss)
                app = QApplication.instance()
                if app:
                    app.setStyleSheet(processed)
                    AppCntxt.data.style_update()
                    self._logger.info("Applied custom QSS stylesheet (fallback).")
        except Exception as e:
            self._logger.error(f"Failed to apply QSS stylesheet: {e}")

    def setup_thread_manager_tab(self):
        hor_layout = QHBoxLayout()
        hor_layout.setContentsMargins(0, 0, 0, 0)

        # --- Async Task Section ---
        async_group = QGroupBox("Async Task (Coroutine)")
        async_layout = QFormLayout(async_group)
        run_async_btn = QPushButton("Run Async Task (sleeps 5s)")
        self.async_status_label = QLabel("Status: Idle")
        async_layout.addRow(run_async_btn)
        async_layout.addRow(self.async_status_label)
        hor_layout.addWidget(async_group)

        # --- Blocking Task Section ---
        blocking_group = QGroupBox("Blocking Task (Thread Pool)")
        blocking_layout = QFormLayout(blocking_group)
        run_blocking_btn = QPushButton("Run Blocking Task (sleeps 5s)")
        self.blocking_status_label = QLabel("Status: Idle")
        blocking_layout.addRow(run_blocking_btn)
        blocking_layout.addRow(self.blocking_status_label)
        hor_layout.addWidget(blocking_group)
        self.thread_layout.addLayout(hor_layout)

        hor_layout1 = QHBoxLayout()
        hor_layout1.setContentsMargins(0, 0, 0, 0)
        # --- Token-Limited Tasks Section ---
        token_group = QGroupBox(f"Token-Limited Tasks (max_tokens={AppCntxt.threader._max_tokens})")
        token_layout = QVBoxLayout(token_group)
        run_token_tasks_btn = QPushButton("Run 20 Token-Limited Tasks")
        token_layout.addWidget(run_token_tasks_btn)
        self.token_status_layout = QVBoxLayout()
        token_layout.addLayout(self.token_status_layout)
        hor_layout1.addWidget(token_group)

        # --- Configuration Section ---
        config_group = QGroupBox("Configuration")
        config_layout = QFormLayout(config_group)
        self.max_workers_spinbox = QSpinBox()
        self.max_workers_spinbox.setRange(1, 32)
        self.max_workers_spinbox.setValue(AppCntxt.threader._max_workers)
        self.max_tokens_spinbox = QSpinBox()
        self.max_tokens_spinbox.setRange(1, 100)
        self.max_tokens_spinbox.setValue(AppCntxt.threader._max_tokens)
        reconfig_btn = QPushButton("Apply and Re-initialize")
        reconfig_btn.clicked.connect(self.reconfigure_thread_manager)
        config_layout.addRow("Max Workers:", self.max_workers_spinbox)
        config_layout.addRow("Max Tokens:", self.max_tokens_spinbox)
        config_layout.addRow(reconfig_btn)
        hor_layout1.addWidget(config_group)
        self.thread_layout.addLayout(hor_layout1)

        self.thread_layout.addStretch()

        # --- Connections ---
        run_async_btn.clicked.connect(self.run_sample_async_task)
        run_blocking_btn.clicked.connect(self.run_sample_blocking_task)
        run_token_tasks_btn.clicked.connect(self.run_token_limited_tasks)

    def reconfigure_thread_manager(self):
        """Reconfigures the ThreadManager with new settings."""
        workers = self.max_workers_spinbox.value()
        tokens = self.max_tokens_spinbox.value()
        try:
            AppCntxt.threader.reconfigure(max_workers=workers, max_tokens=tokens)
            self._logger.info(f"ThreadManager reconfigured: workers={workers}, tokens={tokens}")
            # Update the group box title
            token_group = self.thread_tab.findChild(QGroupBox, "Token-Limited Tasks")
            if token_group:
                token_group.setTitle(f"Token-Limited Tasks (max_tokens={tokens})")
        except Exception as e:
            self._logger.error(f"Failed to reconfigure ThreadManager: {e}")

    def run_sample_async_task(self):
        """Schedules a sample coroutine on the ThreadManager."""
        self.async_status_label.setText("Status: Scheduled...")

        async def sample_coro():
            self.update_status_signal.emit(self.async_status_label, "Status: Running (awaiting sleep)...")
            await asyncio.sleep(5)
            self.update_status_signal.emit(self.async_status_label, "Status: Finished.")
            # Reset after a delay
            await asyncio.sleep(6)
            self.update_status_signal.emit(self.async_status_label, "Status: Idle")

        AppCntxt.threader.run_async(sample_coro())

    def run_sample_blocking_task(self):
        """Submits a sample blocking function to the ThreadManager's executor."""
        self.blocking_status_label.setText("Status: Submitted...")

        def sample_fn():
            self.update_status_signal.emit(self.blocking_status_label, "Status: Running (sleeping)...")
            time.sleep(5)
            return "Finished."

        future = AppCntxt.threader.submit_blocking(sample_fn)
        future.add_done_callback(
            lambda f: (
                self.blocking_status_label.setText(f"Status: {f.result()}"),
                # Use QTimer to reset the label after a delay to avoid another thread
                QTimer.singleShot(3000, lambda: self.blocking_status_label.setText("Status: Idle"))
            )
        )

    def run_token_limited_tasks(self):
        """Runs multiple tasks that compete for a limited number of tokens."""
        self.clear_layout(self.token_status_layout)
        task_labels = [QLabel(f"Task {i+1}: Waiting...") for i in range(20)]
        for label in task_labels:
            self.token_status_layout.addWidget(label)

        def token_worker(task_num: int, label: QLabel):
            self.update_status_signal.emit(label, f"Task {task_num}: Waiting for token...")
            # Use the blocking context manager for simplicity in a worker thread
            with AppCntxt.threader.token():
                self.update_status_signal.emit(label, f"Task {task_num}: Acquired token, working (1.5s)...")
                time.sleep(1.5)
                self.update_status_signal.emit(label, f"Task {task_num}: Releasing token, finished.")

        # Submit all tasks to the thread pool
        for i, label in enumerate(task_labels):
            AppCntxt.threader.submit_blocking(token_worker, i + 1, label)

    def setup_data_tab(self):
        """Sets up the UI for testing the AppData class."""
        # --- Progress Bar Section ---
        progress_group = QGroupBox("Progress Bar Signal Test")
        progress_layout = QFormLayout(progress_group)

        self.test_progress_bar = QProgressBar()
        self.test_progress_bar.setRange(0, 100)
        AppCntxt.data.register_progressbar(self.test_progress_bar)

        self.progress_value_spinbox = QSpinBox()
        self.progress_value_spinbox.setRange(0, 100)
        self.progress_message_input = QLineEdit("Working...")
        set_progress_btn = QPushButton("Call AppData.set_progress()")
        set_progress_btn.clicked.connect(self.test_set_progress)

        progress_layout.addRow("Test Progress Bar:", self.test_progress_bar)
        progress_layout.addRow("Value:", self.progress_value_spinbox)
        progress_layout.addRow("Message:", self.progress_message_input)
        progress_layout.addRow(set_progress_btn)
        self.data_layout.addWidget(progress_group)

        # --- Style Signal Section ---
        style_group = QGroupBox("Style Signal Test")
        style_layout = QFormLayout(style_group)
        emit_style_btn = QPushButton("Call AppData.style_update()")
        emit_style_btn.clicked.connect(AppCntxt.data.style_update)
        self.style_signal_status = QLabel("Status: Idle. Click button to emit signal.")
        AppCntxt.data.style_changed.connect(self.on_style_signal_received)

        style_layout.addRow(emit_style_btn)
        style_layout.addRow(self.style_signal_status)
        self.data_layout.addWidget(style_group)

        # --- Data Store Section ---
        data_store_group = QGroupBox("Shared Data Store Test")
        data_store_layout = QFormLayout(data_store_group)
        self.data_key_input = QLineEdit("my_key")
        self.data_value_input = QLineEdit("my_value")
        set_data_btn = QPushButton("Set Data")
        set_data_btn.clicked.connect(self.test_set_data)

        self.data_get_key_input = QLineEdit("my_key")
        get_data_btn = QPushButton("Get Data")
        get_data_btn.clicked.connect(self.test_get_data)
        self.retrieved_data_label = QLabel("Retrieved Value: (none)")

        clear_data_btn = QPushButton("Clear All Data")
        clear_data_btn.clicked.connect(self.test_clear_data)

        data_store_layout.addRow("Key:", self.data_key_input)
        data_store_layout.addRow("Value:", self.data_value_input)
        data_store_layout.addRow(set_data_btn)
        data_store_layout.addRow(QHBoxLayout()) # Spacer
        data_store_layout.addRow("Key to Get:", self.data_get_key_input)
        data_store_layout.addRow(get_data_btn)
        data_store_layout.addRow(self.retrieved_data_label)
        data_store_layout.addRow(QHBoxLayout()) # Spacer
        data_store_layout.addRow(clear_data_btn)
        self.data_layout.addWidget(data_store_group)

        self.data_layout.addStretch()

    def test_set_progress(self):
        """Calls the global progress update method in AppData."""
        value = self.progress_value_spinbox.value()
        message = self.progress_message_input.text()
        AppCntxt.data.set_progress(value, message)

    def on_style_signal_received(self):
        """Slot to handle the style_changed signal from AppData."""
        self.style_signal_status.setText("Status: Received 'style_changed' signal!")
        # Reset after a delay
        QTimer.singleShot(3000, lambda: self.style_signal_status.setText("Status: Idle."))

    def test_set_data(self):
        """Calls AppData.set_data with values from the UI."""
        key = self.data_key_input.text()
        value = self.data_value_input.text()
        if key:
            AppCntxt.data.set_data(key, value)
            self._logger.info(f"Set data: '{key}' = '{value}'")

    def test_get_data(self):
        """Calls AppData.get_data and displays the result."""
        key = self.data_get_key_input.text()
        if key:
            value = AppCntxt.data.get_data(key, default="<Not Found>")
            self.retrieved_data_label.setText(f"Retrieved Value: {value}")
            self._logger.info(f"Retrieved data for key '{key}'.")

    def test_clear_data(self):
        """Calls AppData.clear_data."""
        AppCntxt.data.clear_data()
        self.retrieved_data_label.setText("Retrieved Value: (store cleared)")
        self._logger.info("Shared data store cleared.")

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
            # app.setPalette(StyleManager.get_palette())
            self.apply_qss_style()
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
        if not os.path.isdir(self.font_path_abs):
            self.font_display_layout.addWidget(QLabel("Font directory not found."))
            return

        for filename in os.listdir(self.font_path_abs):
            if filename.lower().endswith(('.ttf', '.otf')):
                full_path = os.path.join(self.font_path_abs, filename)
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
            preview_label.setMinimumHeight(100)

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
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setMaximumHeight(1)
            # separator.setFrameShadow(QFrame.Sunken)
            entry_layout.addWidget(separator)

            self.font_display_layout.addLayout(entry_layout)

    def setup_icon_tab(self):
        # Set path relative to this script's location

        # --- Controls ---
        controls_layout = QFormLayout()
        self.icon_color_combo = QComboBox()
        self.icon_size_input = QSpinBox()
        self.icon_size_input.setRange(8, 300)
        self.icon_size_input.setValue(55)

        # --- Search and Refresh Controls ---
        self.icon_search_input = QLineEdit()
        self.icon_search_input.setPlaceholderText("Search icons...")
        # Search is now triggered by the button, not textChanged
        self.search_icons_btn = QPushButton("Search")
        self.refresh_icons_btn = QPushButton("Refresh List")

        # Load new icons button
        load_icon_btn = QPushButton("Load New Icon(s)")

        # Add controls
        controls_layout.addRow("Color:", self.icon_color_combo)
        controls_layout.addRow("Size:", self.icon_size_input)
        controls_layout.addRow("Search:", self.icon_search_input)
        button_row = QHBoxLayout()
        button_row.addWidget(self.search_icons_btn)
        button_row.addWidget(self.refresh_icons_btn)
        button_row.addWidget(load_icon_btn)
        controls_layout.addRow(button_row)

        self.icon_layout.addLayout(controls_layout)

        # --- Icon Display Area ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.icon_grid_widget = QWidget()
        self.icon_grid_layout = QGridLayout(self.icon_grid_widget)
        scroll.setWidget(self.icon_grid_widget)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.icon_layout.addWidget(scroll)

        # --- Loading Indicator ---
        self.loading_label = QLabel("Loading icons...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.hide()  # hidden until loading starts
        self.icon_layout.addWidget(self.loading_label)

        # --- Connect signals ---
        self.search_icons_btn.clicked.connect(self.update_icon_display)
        self.refresh_icons_btn.clicked.connect(self.refresh_icons)
        load_icon_btn.clicked.connect(self.load_new_icons)
        self.icon_color_combo.currentTextChanged.connect(self.update_icon_display)
        # self.icon_size_input.valueChanged.connect(self.update_icon_display)

        # Connect the notifier from IconManager ONCE.
        if not self._icon_notifier_connected:
            try:
                IconManager._notifier.icon_loaded.connect(self._on_icon_loaded)
                self._icon_notifier_connected = True
            except Exception as e:
                self._logger.error(f"Failed to connect icon notifier: {e}")

        self.update_icon_display()

    def refresh_icons(self):
        """Refresh icon list from disk and reload display."""
        IconManager.list_icons()  # Force re-scan of the directory
        self.icon_search_input.clear() # Clear search on full refresh
        self.update_icon_display()

    def update_icon_display(self):
        # Increment generation to invalidate results from previous loads
        self._icon_load_generation += 1
        current_generation = self._icon_load_generation

        # Clear existing grid and state
        self.clear_layout(self.icon_grid_layout)
        self._icon_label_map.clear()
        self._loaded_count = 0
        self._loading_total = 0

        # Show loading label
        self.loading_label.show()

        color_key = self.icon_color_combo.currentText()
        if not color_key:
            self.loading_label.setText("No color selected.")
            return

        color = StyleManager.get_colour(color_key)
        size = self.icon_size_input.value()

        # --- Get filtered list of icons to display ---
        search_text = self.icon_search_input.text()
        all_icons = IconManager.list_icons()
        icon_names = IconManager.search_icons(search_text, all_icons)

        if not icon_names:
            self.loading_label.setText("No icons found.")
            return

        self._loading_total = len(icon_names)
        self.loading_label.setText(f"Loading 0/{self._loading_total} icons...")

        # --- Create placeholders and request async loads ---
        cols = 5
        for idx, name in enumerate(icon_names):
            row, col = divmod(idx, cols)

            # Create placeholder widgets
            icon_label = QLabel()
            icon_label.setFixedSize(size, size)
            icon_label.setAlignment(Qt.AlignCenter)
            name_label = QLabel(name.replace('_', ' '))
            name_label.setWordWrap(True)
            name_label.setAlignment(Qt.AlignCenter)

            cell_widget = QWidget()
            cell_layout = QVBoxLayout(cell_widget)
            cell_layout.addWidget(icon_label)
            cell_layout.addWidget(name_label)
            self.icon_grid_layout.addWidget(cell_widget, row, col)

            # Map the icon name to its label for async update
            self._icon_label_map[name] = icon_label

            # Request the icon, IconManager will load it in the background
            try:
                IconManager.get_pixmap(name, color, size, async_load=True)
            except FileNotFoundError:
                self._loading_total -= 1 # Decrement total if file is missing

        if self._loading_total <= 0:
            self.loading_label.setText("No icons found.")

    def _on_icon_loaded(self, name: str, image: QImage):
        """Slot connected to IconManager's notifier. Receives QImage from worker thread."""
        # Discard signal if it's from a previous, obsolete loading operation
        if self._icon_load_generation != getattr(self, '_icon_load_generation', 0):
            return

        if name in self._icon_label_map:
            label = self._icon_label_map[name]
            # Convert thread-safe QImage to QPixmap in the main GUI thread
            pixmap = QPixmap.fromImage(image)
            if not pixmap.isNull():
                label.setPixmap(pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

            self._loaded_count += 1
            self.loading_label.setText(f"Loading {self._loaded_count}/{self._loading_total} icons...")

            if self._loaded_count >= self._loading_total:
                self.loading_label.hide()

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

        self.refresh_icons()

    def reload_ui(self):
        # Clear layouts
        self.settings_tab_widget.clear() # Clear the new tab widget
        self.clear_layout(self.palette_layout)

        accent = self._config.get_value('accent')
        support = self._config.get_value('support')
        neutral = self._config.get_value('neutral')
        theme = self._config.get_value('theme')

        # --- Populate Settings Tab ---
        self.combos = {}
        self.lineedits = {}
        theme_keys = ['accent', 'support', 'neutral', 'theme']

        # Group user settings by their 'group' property
        user_settings = self._config.data.configuration.user
        grouped_settings = {}
        for key, setting in user_settings.items():
            # if key in theme_keys:
            #     continue  # Skip theme settings, they are on the palette tab
            group_name = setting.group or "General"
            if group_name not in grouped_settings:
                grouped_settings[group_name] = []
            grouped_settings[group_name].append((key, setting))

        # Create a tab for each group
        for group_name, settings_list in sorted(grouped_settings.items()):
            group_tab = QWidget()
            group_layout = QFormLayout(group_tab)

            for key, setting in settings_list:
                label = QLabel(setting.name)
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked=False, k=key: self.delete_setting(k))
                row = QHBoxLayout()

                if setting.type == "dropdown":
                    combo = QComboBox()
                    combo.addItems(setting.values)
                    combo.setCurrentText(setting.value)
                    combo.currentTextChanged.connect(lambda val, k=key: self.on_setting_changed(k, val))
                    row.addWidget(combo)
                    self.combos[key] = combo
                elif setting.type in ["text", "filebrowse", "folderbrowse", "file_browse", "folder_browse"]:
                    lineedit = QLineEdit()
                    lineedit.setText(str(setting.value))
                    lineedit.editingFinished.connect(lambda k=key, le=lineedit: self.on_text_setting_changed(k, le))
                    row.addWidget(lineedit)
                    self.lineedits[key] = lineedit

                    if setting.type in ["filebrowse", "file_browse"]:
                        browse_btn = QPushButton("Browse...")
                        browse_btn.clicked.connect(lambda checked=False, le=lineedit, k=key: self.browse_for_file(le, k))
                        row.addWidget(browse_btn)
                    elif setting.type in ["folderbrowse", "folder_browse"]:
                        browse_btn = QPushButton("Browse...")
                        browse_btn.clicked.connect(lambda checked=False, le=lineedit, k=key: self.browse_for_folder(le, k))
                        row.addWidget(browse_btn)
                else:
                    lineedit = QLineEdit()
                    lineedit.setText(str(setting.value))
                    lineedit.setReadOnly(True)
                    row.addWidget(lineedit)

                row.addWidget(delete_btn)
                group_layout.addRow(label, row)

            self.settings_tab_widget.addTab(group_tab, group_name)

        # Static settings (always as read-only textboxes in a "Static" tab)
        static_tab = QWidget()
        static_layout = QFormLayout(static_tab)
        static_settings = self._config.data.configuration.static
        for key, value in static_settings.items():
            label = QLabel(key)
            lineedit = QLineEdit()
            lineedit.setText(str(value))
            lineedit.setReadOnly(True)
            static_layout.addRow(label, lineedit)
        self.settings_tab_widget.addTab(static_tab, "Static Settings")


        # --- Add New Setting Form in its own tab ---
        add_setting_tab = QWidget()
        new_setting_layout = QFormLayout(add_setting_tab)

        self.new_setting_key = QLineEdit()
        self.new_setting_name = QLineEdit()
        self.new_setting_value = QLineEdit()
        self.new_setting_type = QComboBox()
        self.new_setting_type.addItems(["text", "dropdown", "file_browse", "folder_browse"])
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

        self.settings_tab_widget.addTab(add_setting_tab, "+ Add New")

        # --- Populate Palette Tab ---
        # Theme settings dropdowns
        theme_settings_layout = QFormLayout()
        for key in theme_keys:
            if key not in user_settings:
                continue
            setting = user_settings[key]
            combo = QComboBox()
            combo.addItems(setting.values)
            combo.setCurrentText(setting.value)
            combo.currentTextChanged.connect(lambda val, k=key: self.on_setting_changed(k, val))

            if key in ['accent', 'support', 'neutral']:
                picker_btn = QPushButton("Pick Color")
                picker_btn.clicked.connect(lambda checked=False, k=key: self.open_color_picker(k))
                row = QHBoxLayout()
                row.addWidget(combo)
                row.addWidget(picker_btn)
                theme_settings_layout.addRow(QLabel(setting.name), row)
            else:
                theme_settings_layout.addRow(QLabel(setting.name), combo)

            self.combos[key] = combo

        palette_container = QWidget()
        palette_main_layout = QVBoxLayout(palette_container)
        palette_main_layout.addLayout(theme_settings_layout)

        # Palette grid
        StyleManager.initialise(accent, support, neutral, theme=theme)

        palette_grid = QGridLayout()
        palette_grid.setSpacing(16)
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
        if 'accent' in color_keys:
            self.icon_color_combo.setCurrentText('accent')
        self.icon_color_combo.blockSignals(False)

        self.apply_qss_style()
        self.setPalette(StyleManager.get_palette())
        AppCntxt.data.style_update()
        # self.update_icon_display() # This can cause excessive reloads, called explicitly now

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
        # No reload_ui() here to avoid losing focus

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

    def browse_for_file(self, lineedit: QLineEdit, key: str):
        """Opens a file dialog and updates the line edit and setting."""
        path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if path:
            lineedit.setText(path)
            self.on_text_setting_changed(key, lineedit)

    def browse_for_folder(self, lineedit: QLineEdit, key: str):
        """Opens a folder dialog and updates the line edit and setting."""
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path:
            lineedit.setText(path)
            self.on_text_setting_changed(key, lineedit)

    def open_color_picker(self, key: str):
        """Opens a QColorDialog and adds the selected color to the setting's values."""
        setting = self._config.data.configuration.user.get(key)
        if not setting:
            return

        initial_color = QColor(setting.value)
        color = QColorDialog.getColor(initial_color, self, f"Select {setting.name}")

        if color.isValid():
            hex_color = color.name()
            if hex_color not in setting.values:
                setting.values.append(hex_color)
                # No direct method to update just the values list, so we update the whole item
                self._config.add_user_setting(key, setting)
                self._logger.info(f"Added new color '{hex_color}' to '{key}' setting.")
                self.reload_ui()

    def closeEvent(self, event, /):
        if self._server:
            self.stop_server()
        self._config.save()
        event.accept()

def run():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == "__main__":
    run()
