import sys
import shutil
from pathlib import Path
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox


def copy_svgs_flat():
    app = QApplication(sys.argv)

    # Select source folder
    source_dir = QFileDialog.getExistingDirectory(None, "Select Source Folder")
    if not source_dir:
        QMessageBox.warning(None, "Warning", "No source folder selected!")
        return

    # Select destination folder
    dest_dir = QFileDialog.getExistingDirectory(None, "Select Destination Folder")
    if not dest_dir:
        QMessageBox.warning(None, "Warning", "No destination folder selected!")
        return

    source_path = Path(source_dir)
    dest_path = Path(dest_dir)

    copied_files = 0

    # Walk through source and find SVGs
    for svg_file in source_path.rglob("*.svg"):
        print(svg_file)
        parts = svg_file.parts
        if len(parts) < 4:
            continue

        # Build new filename: parent3_parent2_parent1_originalname.svg
        new_name = "_".join(parts[-4:-1] + (svg_file.name,))

        dest_file = dest_path / new_name

        shutil.copy(svg_file, dest_file)
        copied_files += 1

    QMessageBox.information(None, "Done", f"Copied {copied_files} SVG files.")

    app.exec()


if __name__ == "__main__":
    copy_svgs_flat()
