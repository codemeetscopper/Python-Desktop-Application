from PySide6.QtGui import QFontDatabase, QFont
import os
from itertools import cycle


class FontManager:
    _instance = None

    def __init__(self):
        self._family_cycle = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FontManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self._font_map = {}           # Maps tags like 'h1' to font info
        self._loaded_families = []    # List of loaded font families
        self._family_cycle = None     # Iterator for round-robin font assignment

    def load_font(self, font_path: str, tag: str = None, size: int = None):
        """
        Loads a TTF font and optionally maps it to a tag with a size.
        If tag/size is not provided, font is added to the pool for round-robin mapping.
        """
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Font file not found: {font_path}")

        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            raise RuntimeError(f"Failed to load font: {font_path}")

        families = QFontDatabase.applicationFontFamilies(font_id)
        if not families:
            raise RuntimeError(f"No font families found in: {font_path}")

        family = families[0]
        self._loaded_families.append(family)
        self._family_cycle = cycle(self._loaded_families)

        if tag:
            self._font_map[tag] = {
                'family': family,
                'size': size if size else 12  # Default size
            }

    def get_font(self, tag: str) -> QFont:
        """
        Returns a QFont object for the given tag.
        If tag is not mapped, assigns a font from the pool.
        """
        if tag not in self._font_map:
            # Assign a font from the pool if available
            if not self._loaded_families:
                raise RuntimeError("No fonts loaded to assign.")

            family = next(self._family_cycle)
            self._font_map[tag] = {
                'family': family,
                'size': 12  # Default size
            }

        font_info = self._font_map[tag]
        return QFont(font_info['family'], font_info['size'])

    def get_font_map(self):
        return self._font_map
