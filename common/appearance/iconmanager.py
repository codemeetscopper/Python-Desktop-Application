import os
from typing import Optional, Dict, List
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

class IconManager:
    _icon_cache: Dict[str, QPixmap] = {}
    _images_path: str = r"resources/images/meterialicons/"  # Default path

    @classmethod
    def get_pixmap(cls, name: str, color: str = "#FFFFFF", size: int = 24) -> QPixmap:
        """
        Get a QPixmap for a given SVG icon name.
        The name should be the filename without the .svg extension.
        """
        cache_key = f"{name}|{color}|{size}"
        if cache_key in cls._icon_cache:
            return QPixmap(cls._icon_cache[cache_key])

        file_path = os.path.join(cls._images_path, f"{name}.svg")
        if not os.path.exists(file_path):
            print(f"Icon not found at {file_path}")
            return QPixmap()

        with open(file_path, "r", encoding="utf-8") as f:
            svg_content = f.read()
        # A simple way to replace fill color. Might not work for all SVGs.
        svg_content = svg_content.replace('fill="#000000"', f'fill="{color}"')

        svg_bytes = QByteArray(svg_content.encode("utf-8"))
        svg_renderer = QSvgRenderer(svg_bytes)

        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        svg_renderer.render(painter)
        painter.end()

        cls._icon_cache[cache_key] = QPixmap(pixmap)
        return pixmap

    @classmethod
    def clear_cache(cls):
        cls._icon_cache.clear()

    @classmethod
    def list_icons(cls) -> List[str]:
        """Lists all available icon names (filenames without extension)."""
        if not os.path.isdir(cls._images_path):
            return []
        return [
            os.path.splitext(f)[0]
            for f in os.listdir(cls._images_path)
            if f.lower().endswith(".svg")
        ]

    @classmethod
    def set_images_path(cls, path: str):
        cls._images_path = path
        cls.clear_cache()

    @classmethod
    def get_images_path(cls) -> str:
        return cls._images_path
