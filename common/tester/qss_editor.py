from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel,
    QFileDialog, QColorDialog, QGroupBox, QLineEdit, QComboBox, QListWidget,
    QProgressBar, QTabWidget, QApplication, QMessageBox, QSplitter
)

from common.appearance.qssmanager import QSSManager
from common import AppCntxt, initialise_context
from common.appearance.stylemanager import StyleManager

_log = logging.getLogger(__name__)


class QssEditorWidget(QWidget):
    """A compact QSS editor with demo controls, translation view, and file operations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        initialise_context()
        self._load_default_qss()

    def _setup_ui(self):
        main = QVBoxLayout(self)
        ctrl_row = QHBoxLayout()
        self.open_btn = QPushButton("Open...")
        self.save_btn = QPushButton("Save...")
        self.load_sample_btn = QPushButton("Load Sample")
        self.reset_btn = QPushButton("Reset")
        self.pick_accent_btn = QPushButton("Pick Accent")
        self.apply_demo_btn = QPushButton("Apply to Demo")
        self.apply_app_btn = QPushButton("Apply to Application")

        ctrl_row.addWidget(self.open_btn)
        ctrl_row.addWidget(self.save_btn)
        ctrl_row.addWidget(self.load_sample_btn)
        ctrl_row.addWidget(self.reset_btn)
        ctrl_row.addStretch()
        ctrl_row.addWidget(self.pick_accent_btn)
        ctrl_row.addWidget(self.apply_demo_btn)
        ctrl_row.addWidget(self.apply_app_btn)
        main.addLayout(ctrl_row)

        # --- Splitter with input + translated QSS ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_box = QVBoxLayout()
        right_box = QVBoxLayout()

        # Left text editor (raw QSS)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_label = QLabel("Raw QSS Editor:")
        self.editor = QTextEdit()
        self.editor.setAcceptRichText(False)
        self.editor.setFont(QFont("Courier", 10))
        left_layout.addWidget(left_label)
        left_layout.addWidget(self.editor)

        # Right text editor (translated/processed QSS)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_label = QLabel("Translated QSS:")
        self.translated_view = QTextEdit()
        self.translated_view.setReadOnly(True)
        self.translated_view.setFont(QFont("Courier", 10))
        right_layout.addWidget(right_label)
        right_layout.addWidget(self.translated_view)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 2)
        main.addWidget(splitter, 3)

        # Status bar
        status_row = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        status_row.addWidget(self.progress)
        main.addLayout(status_row)

        # Demo area
        demo_group = QGroupBox("Demo Preview (styles applied here)")
        demo_layout = QVBoxLayout(demo_group)
        top_row = QHBoxLayout()
        self.demo_button = QPushButton("Demo Button")
        self.demo_line = QLineEdit("Sample text")
        self.demo_combo = QComboBox()
        self.demo_combo.addItems(["Option 1", "Option 2", "Option 3"])
        top_row.addWidget(self.demo_button)
        top_row.addWidget(self.demo_line)
        top_row.addWidget(self.demo_combo)
        demo_layout.addLayout(top_row)

        tabs = QTabWidget()
        tab1 = QWidget()
        t1l = QVBoxLayout(tab1)
        self.demo_list = QListWidget()
        for i in range(6):
            self.demo_list.addItem(f"Item {i+1}")
        t1l.addWidget(self.demo_list)
        tabs.addTab(tab1, "List")

        tab2 = QWidget()
        t2l = QVBoxLayout(tab2)
        self.demo_progress = QProgressBar()
        self.demo_progress.setValue(45)
        t2l.addWidget(self.demo_progress)
        tabs.addTab(tab2, "Progress")

        demo_layout.addWidget(tabs)
        main.addWidget(demo_group, 2)

        # connections
        self.open_btn.clicked.connect(self.open_file)
        self.save_btn.clicked.connect(self.save_file)
        self.load_sample_btn.clicked.connect(self._load_default_qss)
        self.reset_btn.clicked.connect(self.reset_demo_styles)
        self.pick_accent_btn.clicked.connect(self.pick_accent_color)
        self.apply_demo_btn.clicked.connect(lambda: self.apply_qss(to_application=False))
        self.apply_app_btn.clicked.connect(lambda: self.apply_qss(to_application=True))

    def _load_default_qss(self):
        # Placeholder: load your default qss string here
        default_qss = """
/* 
   Use key inside <> to insert colors from the current palette. 
   Examples: <accent>, <support>, <neutral>, <bg>, <fg> * Lightness modifiers are also available: 
   e.g., <accent_l1>,<accent_l2>,<accent_l3>,<accent_d1>,<accent_d2>,<accent_d3>,
   <support_l1>,<support_l2>,<support_l3>,<support_d1>,<support_d2>,<support_d3>, 
   <neutral_l1>,<neutral_l2>,<neutral_l3>,<neutral_d1>,<neutral_d2>,<neutral_d3>,
   <bg1>,<bg2>,
   <fg1>,<fg2>,
*/

/* ===========================
   BUTTONS
   =========================== */
QWidget {
    background-color: <bg2>;
    color: <support_d3>;
}

QPushButton {
    background-color: <support>;
    color: white;
    border: 0px solid <accent_d1>;
    padding: 5px 10px;
    border-radius: 4px;
    min-height: 25px;
    min-width: 75px;
    max-width: 150px;
}
QPushButton:hover {
    background-color: <accent_l1>;
}
QPushButton:pressed {
    background-color: <accent_d1>;
}
QPushButton:disabled {
    background-color: <bg2>;
    color: <fg2>;
}

/* ===========================
   INPUTS & TEXT
=========================== */
QLineEdit, QTextEdit, QPlainTextEdit {
    border: 1px solid <neutral>;
    border-radius: 4px;
    padding: 4px;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid <accent>;
}
QLabel {
    color: <fg>;
    background: transparent;
}

/* ===========================
   COMBOBOX
=========================== */
QComboBox {
    border: 1px solid <neutral>;
    border-radius: 4px;
    padding: 3px 6px;
}
QComboBox:hover {
    border: 1px solid <accent>;
}
QComboBox::drop-down {
    width: 20px;
    border-left: 1px solid <neutral>;
}
QComboBox::down-arrow {
    image: <img: hardware keyboard arrow down; color:accent>;
    width: 10px;
    height: 10px;
}

/* ===========================
   TAB WIDGET
=========================== */
QTabWidget::pane {
    border-top: 2px solid <accent>;
}
QTabBar::tab {
    padding: 8px 12px;
    border: 0;
}
QTabBar::tab:selected, QTabBar::tab:hover {
    background: <accent>;
    color: white;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

/* ===========================
   SCROLLBARS
=========================== */
QScrollBar:horizontal, QScrollBar:vertical {
    border: none;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle {
    background: <neutral>;
    border-radius: 4px;
}
QScrollBar::handle:hover {
    background: <neutral_d1>;
}
QScrollBar::add-line, QScrollBar::sub-line {
    border: none;
    width: 0;
    height: 0;
}

/* ===========================
   CHECKBOX & RADIO
=========================== */
QCheckBox, QRadioButton {
    spacing: 6px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid <neutral>;
    border-radius: 3px;
    background: <bg1>;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background: <accent>;
    border: 1px solid <accent>;
}
QRadioButton::indicator {
    border-radius: 8px;
}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border: 1px solid <accent>;
}

/* ===========================
   MENU & TOOLBUTTON
=========================== */
QMenuBar {
    background: <bg>;
    color: <fg>;
}
QMenuBar::item {
    padding: 4px 10px;
    background: transparent;
}
QMenuBar::item:selected {
    background: <accent_l1>;
    color: <bg>;
}
QMenu {
    background: <bg1>;
    border: 1px solid <neutral>;
}
QMenu::item {
    padding: 5px 20px;
    color: <fg>;
}
QMenu::item:selected {
    background: <accent>;
    color: <bg>;
}
QToolButton {
    background: transparent;
    border: none;
    color: <fg>;
    padding: 4px;
}
QToolButton:hover {
    background: <bg2>;
}
QToolButton:checked {
    background: <accent>;
    color: <bg>;
    border-radius: 4px;
}

/* ===========================
   SLIDERS
=========================== */
QSlider::groove:horizontal {
    height: 6px;
    background: <bg2>;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: <accent>;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QSlider::handle:horizontal:hover {
    background: <accent_l1>;
}
QSlider::groove:vertical {
    width: 6px;
    background: <bg2>;
    border-radius: 3px;
}
QSlider::handle:vertical {
    background: <accent>;
    height: 14px;
    margin: 0 -5px;
    border-radius: 7px;
}

/* ===========================
   PROGRESS BAR
=========================== */
QProgressBar {
    border: 1px solid <neutral>;
    border-radius: 4px;
    text-align: center;
    height: 18px;
}
QProgressBar::chunk {
    background-color: <accent>;
    border-radius: 4px;
}

/* ===========================
   TABLES & LISTS
=========================== */
QTableView, QListView, QTreeView {
    border: 1px solid <neutral>;
    gridline-color: <neutral>;
}
QHeaderView::section {
    background: <bg2>;
    color: <fg>;
    padding: 4px;
    border: 1px solid <neutral>;
}
QTableView::item:selected, QListView::item:selected, QTreeView::item:selected {
    background: <accent>;
    color: <bg>;
}
        """.strip()
        self.editor.setPlainText(default_qss)
        self.status_label.setText("Loaded sample QSS")

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open QSS", "", "QSS Files (*.qss *.txt);;All Files (*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.editor.setPlainText(f.read())
            self.status_label.setText(f"Loaded: {Path(path).name}")
        except Exception as e:
            QMessageBox.warning(self, "Open Error", f"Could not open file: {e}")
            _log.exception("Open file failed")

    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save QSS", "", "QSS Files (*.qss *.txt);;All Files (*)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self.status_label.setText(f"Saved: {Path(path).name}")
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Could not save file: {e}")
            _log.exception("Save file failed")

    def pick_accent_color(self):
        try:
            if AppCntxt.styler:
                current = AppCntxt.styler.get_colour('accent')
            else:
                current = "#4CAF50"
        except Exception:
            current = "#4CAF50"
        color = QColorDialog.getColor(Qt.GlobalColor.white, self, "Pick Accent Colour")
        if color.isValid():
            hexcol = color.name()
            support = AppCntxt.styler.get_colour('support') if AppCntxt.styler else "#FF9800"
            neutral = AppCntxt.styler.get_colour('neutral') if AppCntxt.styler else "#9E9E9E"
            theme = "light"
            try:
                AppCntxt.styler.initialise(hexcol, support, neutral, theme)
                self.status_label.setText(f"StyleManager initialised with accent {hexcol}")
            except Exception as e:
                _log.exception("Failed to initialise StyleManager: %s", e)
                self.status_label.setText("Failed to set accent colour")

    def apply_qss(self, to_application: bool = False):
        raw = self.editor.toPlainText()
        try:
            self.progress.setVisible(True)
            self.progress.setValue(0)
            processed = QSSManager.process(raw)
            self.progress.setValue(60)

            # --- show translated qss ---
            self.translated_view.setPlainText(processed)

            if to_application:
                app = QApplication.instance()
                if app:
                    app.setStyleSheet(processed)
                    self.status_label.setText("Applied stylesheet to application")
                else:
                    self.status_label.setText("No QApplication instance found")
            else:
                demo_group = self.findChild(QGroupBox)
                if demo_group:
                    demo_group.setStyleSheet(processed)
                    self.status_label.setText("Applied stylesheet to demo preview")
                else:
                    self.status_label.setText("Demo preview not found")

            self.progress.setValue(100)
        except Exception as e:
            _log.exception("Failed to apply QSS: %s", e)
            QMessageBox.warning(self, "QSS Error", f"Failed to apply QSS: {e}")
            self.status_label.setText("Failed to apply stylesheet")
        finally:
            self.progress.setVisible(False)

    def reset_demo_styles(self):
        demo_group = self.findChild(QGroupBox)
        if demo_group:
            demo_group.setStyleSheet("")
        app = QApplication.instance()
        if app:
            app.setStyleSheet("")
        self.status_label.setText("Styles reset")


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = QssEditorWidget()
    w.resize(1100, 700)
    w.show()
    sys.exit(app.exec())
