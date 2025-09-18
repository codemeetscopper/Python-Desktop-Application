import logging

from common.logger import QtLogger

# ---------------- Example usage ----------------
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QTextEdit, QVBoxLayout, QWidget
    import sys

    app = QApplication([])

    logger = QtLogger()

    class LogViewer(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Log Viewer")
            self.resize(600, 400)

            layout = QVBoxLayout()
            self.text_edit = QTextEdit()
            self.text_edit.setReadOnly(True)
            layout.addWidget(self.text_edit)
            self.setLayout(layout)

            logger.log_updated.connect(self.append_log)

        def append_log(self, msg: str):
            self.text_edit.append(msg)

    viewer = LogViewer()
    viewer.show()

    @logger.log_function()
    def add(a, b):
        return a + b

    @logger.log_function(level=logging.INFO)
    def greet(name):
        return f"Hello, {name}!"

    add(5, 7)
    greet("Aby")
    logger.info("Custom info message")

    logger.export_to_file("app_log.txt")

    sys.exit(app.exec())
