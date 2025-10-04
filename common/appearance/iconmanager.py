import os
import re
from typing import Dict, List
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer


class IconManager:
    _icon_cache: Dict[str, QPixmap] = {}
    _images_path: str = r"resources/images/meterialicons/"

    @classmethod
    def get_pixmap(cls, name: str, color: str = "#FFFFFF", size: int = 24) -> QPixmap:
        """
        Load an SVG icon and apply a color tint (affects only non-transparent parts).
        """
        cache_key = f"{name}|{color.lower()}|{size}"
        if cache_key in cls._icon_cache:
            return QPixmap(cls._icon_cache[cache_key])

        file_path = os.path.join(cls._images_path, f"{name}.svg")
        if not os.path.exists(file_path):
            print(f"[IconManager] Icon not found: {file_path}")
            return QPixmap()

        # --- Render the SVG to a transparent pixmap ---
        svg_renderer = QSvgRenderer(file_path)
        base_pixmap = QPixmap(size, size)
        base_pixmap.fill(Qt.transparent)

        painter = QPainter(base_pixmap)
        svg_renderer.render(painter)
        painter.end()

        # --- Apply the desired color only to non-transparent pixels ---
        tinted = QPixmap(size, size)
        tinted.fill(Qt.transparent)

        painter = QPainter(tinted)
        painter.drawPixmap(0, 0, base_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), QColor(color))
        painter.end()

        cls._icon_cache[cache_key] = QPixmap(tinted)
        return tinted

    @classmethod
    def clear_cache(cls):
        cls._icon_cache.clear()

    @classmethod
    def list_icons(cls) -> List[str]:
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
