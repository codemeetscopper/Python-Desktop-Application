import subprocess
import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QLineEdit, QLabel, QTextEdit, QMessageBox, QHBoxLayout
)
from PySide6.QtCore import QThread, Signal


class PyreverseWorker(QThread):
    log_signal = Signal(str)
    finished_signal = Signal(bool, list)

    def __init__(self, source_path: str, output_path: str):
        super().__init__()
        self.source_path = source_path
        self.output_path = output_path
        self.errors = []

    def safe_log(self, msg, error=False):
        """Helper to log messages and track errors"""
        self.log_signal.emit(msg)
        if error:
            self.errors.append(msg)

    def run(self):
        try:
            src = Path(self.source_path)
            out = Path(self.output_path)

            if not src.exists():
                self.safe_log("❌ Source path does not exist.", error=True)
                self.finished_signal.emit(False, self.errors)
                return

            out.mkdir(parents=True, exist_ok=True)

            py_files = list(src.rglob("*.py"))
            if not py_files:
                self.safe_log("⚠️ No Python files found in source path.", error=True)
                self.finished_signal.emit(False, self.errors)
                return

            self.log_signal.emit(f"📂 Found {len(py_files)} Python files.")

            # Run pyreverse for each file
            for py_file in py_files:
                try:
                    module_name = py_file.stem  # filename without extension
                    cmd = ["pyreverse", "-o", "png", "-p", module_name, str(py_file)]
                    self.log_signal.emit(f"⚙️ Running: {' '.join(cmd)}")

                    process = subprocess.Popen(
                        cmd, cwd=src, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    stdout, stderr = process.communicate()

                    if stdout:
                        self.log_signal.emit(stdout)
                    if stderr:
                        self.safe_log(stderr, error=True)

                    # Expected generated files
                    expected_files = {
                        f"classes_{module_name}.png": f"{module_name}_classes.png",
                        f"packages_{module_name}.png": f"{module_name}_packages.png"
                    }

                    for generated_name, renamed in expected_files.items():
                        try:
                            generated = src / generated_name
                            if generated.exists():
                                dest = out / renamed
                                shutil.move(str(generated), dest)
                                self.log_signal.emit(f"✅ Saved {renamed} to {dest}")
                            else:
                                self.safe_log(f"⚠️ Expected {generated_name} not found.", error=True)
                        except Exception as e:
                            self.safe_log(f"❌ Error moving {generated_name}: {e}", error=True)

                except Exception as e:
                    self.safe_log(f"❌ Failed on {py_file.name}: {e}", error=True)

            success = len(self.errors) == 0
            self.finished_signal.emit(success, self.errors)

        except Exception as e:
            self.safe_log(f"❌ Unexpected fatal error: {e}", error=True)
            self.finished_signal.emit(False, self.errors)


class PyreverseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pyreverse UML Generator")
        self.setGeometry(300, 200, 700, 400)

        layout = QVBoxLayout()

        # Source Path
        src_layout = QHBoxLayout()
        self.src_edit = QLineEdit()
        self.src_btn = QPushButton("Browse Source")
        self.src_btn.clicked.connect(self.browse_source)
        src_layout.addWidget(QLabel("Source Path:"))
        src_layout.addWidget(self.src_edit)
        src_layout.addWidget(self.src_btn)
        layout.addLayout(src_layout)

        # Output Path
        out_layout = QHBoxLayout()
        self.out_edit = QLineEdit()
        self.out_btn = QPushButton("Browse Output")
        self.out_btn.clicked.connect(self.browse_output)
        out_layout.addWidget(QLabel("Output Path:"))
        out_layout.addWidget(self.out_edit)
        out_layout.addWidget(self.out_btn)
        layout.addLayout(out_layout)

        # Run Button
        self.run_btn = QPushButton("Run Pyreverse")
        self.run_btn.clicked.connect(self.run_pyreverse)
        layout.addWidget(self.run_btn)

        # Log Area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)

        self.setLayout(layout)

    def browse_source(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.src_edit.setText(folder)

    def browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.out_edit.setText(folder)

    def run_pyreverse(self):
        src_path = self.src_edit.text().strip()
        out_path = self.out_edit.text().strip()

        if not src_path or not out_path:
            QMessageBox.warning(self, "Warning", "Please select both source and output paths.")
            return

        self.log_area.clear()
        self.log("🚀 Starting Pyreverse...")

        self.worker = PyreverseWorker(src_path, out_path)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.finished)
        self.worker.start()

    def log(self, message):
        self.log_area.append(message)

    def finished(self, success, errors):
        if errors:
            err_msg = "\n".join(errors)
            QMessageBox.warning(self, "Completed with Errors",
                                f"⚠️ Process completed but with errors:\n\n{err_msg}")
        elif success:
            QMessageBox.information(self, "Done", "✅ Pyreverse completed successfully!")
        else:
            QMessageBox.critical(self, "Error", "❌ Pyreverse failed. Check logs.")


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = PyreverseApp()
    window.show()
    sys.exit(app.exec())
