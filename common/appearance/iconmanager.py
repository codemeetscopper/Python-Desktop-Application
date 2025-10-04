import os
import re
from typing import Dict, List
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer

from test3 import search_icons


class IconManager:
    _icon_cache: Dict[str, QPixmap] = {}
    _images_path: str = r"resources/images/meterialicons/"
    _icon_list: List[str] = []

    @staticmethod
    def search_icons(query: str, icons: List[str], regex: bool = True) -> List[str]:
        """
        Search for icons in the list.

        :param query: Substring or regex pattern to search for
        :param icons: List of icon names
        :param regex: If True, treat query as regex
        :return: List of matching icon names
        """
        query = query.replace(' ', '_')
        if regex:
            pattern = re.compile(query)
            return [icon for icon in icons if pattern.search(icon)]
        else:
            return [icon for icon in icons if query in icon]

    @classmethod
    def get_pixmap(cls, name: str, color: str = "#FFFFFF", size: int = 24) -> QPixmap:
        """
        Load an SVG icon and apply a color tint (affects only non-transparent parts).
        """
        if len( cls._icon_list) == 0:
            cls.list_icons()
        name_list = search_icons(name, cls._icon_list)
        if name_list:
            name = name_list[0]
        else:
            raise  Exception(f"[IconManager] Icon not found in list: {name}")

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
            cls._icon_list.clear()
            return []
        cls._icon_list = [
            os.path.splitext(f)[0]
            for f in os.listdir(cls._images_path)
            if f.lower().endswith(".svg")
        ]
        return cls._icon_list

    @classmethod
    def set_images_path(cls, path: str):
        cls._images_path = path
        cls.clear_cache()

    @classmethod
    def get_images_path(cls) -> str:
        return cls._images_path
