import shutil
from pathlib import Path


def copy_icons(icon_type: str, src_path: str, dst_path: str) -> int:
    """
    Copy all SVG icons of a specific type (e.g., 'materialiconsround') from src_path to dst_path.

    :param icon_type: Type of icon (e.g., 'materialiconsround')
    :param src_path: Source folder containing all SVG icons
    :param dst_path: Destination folder to copy matching icons
    :return: Number of files copied
    """
    src = Path(src_path)
    dst = Path(dst_path)

    if not src.exists():
        raise FileNotFoundError(f"Source path not found: {src_path}")

    dst.mkdir(parents=True, exist_ok=True)

    copied = 0
    for svg_file in src.glob("*.svg"):
        if icon_type.lower() in svg_file.stem.lower():
            shutil.copy(svg_file, dst / svg_file.name)
            copied += 1

    return copied


# Example usage
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

    app = QApplication(sys.argv)

    icon_type = "materialicons_"

    src_folder = QFileDialog.getExistingDirectory(None, "Select Source (All Icons) Folder")
    if not src_folder:
        QMessageBox.warning(None, "Warning", "No source folder selected!")
        sys.exit()

    dst_folder = QFileDialog.getExistingDirectory(None, f"Select Destination Folder for '{icon_type}' Icons")
    if not dst_folder:
        QMessageBox.warning(None, "Warning", "No destination folder selected!")
        sys.exit()

    count = copy_icons(icon_type, src_folder, dst_folder)
    QMessageBox.information(None, "Done", f"Copied {count} '{icon_type}' icons.")

    app.exec()
