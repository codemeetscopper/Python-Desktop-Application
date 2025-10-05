import os
import threading
from typing import Dict, List, Optional
from PySide6.QtCore import QObject, Signal, Qt, QThreadPool, QRunnable
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer


# ------------------------------
# Internal async worker
# ------------------------------
class _IconLoadTask(QRunnable):
    """Background worker for loading and caching icons."""
    def __init__(self, name: str, color: str, size: int, file_path: str, callback):
        super().__init__()
        self.name = name
        self.color = color
        self.size = size
        self.file_path = file_path
        self.callback = callback

    def run(self):
        pixmap = IconManager._load_icon_pixmap(self.file_path, self.color, self.size)
        if self.callback:
            self.callback(self.name, self.color, self.size, pixmap)


# ------------------------------
# Internal notifier QObject
# ------------------------------
class _IconNotifier(QObject):
    """QObject wrapper so static IconManager can still emit Qt signals."""
    icon_loaded = Signal(str, QPixmap)


# ------------------------------
# Main IconManager class
# ------------------------------
class IconManager:
    """Thread-safe, cached and async-capable SVG icon manager (static API)."""

    # Internal state
    _icon_cache: Dict[str, QPixmap] = {}
    _icon_lock = threading.Lock()
    _images_path: str = r"resources/images/meterialicons/"
    _icon_list: List[str] = []
    _thread_pool = QThreadPool.globalInstance()
    _notifier = _IconNotifier()  # Holds the actual Qt signal object

    # --- Style and size suffix patterns ---
    _style_suffixes = [
        '_materialiconsoutlined',
        '_materialiconsround',
        '_materialiconssharp',
        '_materialiconstwotone',
        '_materialicons'
    ]
    _size_suffixes = ['_20px', '_24px']

    # --------------------------
    # Public APIs
    # --------------------------

    @staticmethod
    def search_icons(query: str, icons: List[str]) -> List[str]:
        """Search for icons in the list, prioritizing matches in the core icon name."""
        query_lower = query.lower().replace(' ', '_')
        if not query_lower:
            return sorted(icons)

        exact_matches, core_matches, substring_matches = [], [], []

        for icon in icons:
            icon_lower = icon.lower()
            if query_lower == icon_lower:
                exact_matches.append(icon)
                continue

            # Extract core name
            core_name = icon_lower
            for suffix in IconManager._size_suffixes + IconManager._style_suffixes:
                if core_name.endswith(suffix):
                    core_name = core_name[: -len(suffix)]
                    break

            if query_lower in core_name:
                core_matches.append(icon)
            elif query_lower in icon_lower:
                substring_matches.append(icon)

        return sorted(exact_matches) + sorted(core_matches) + sorted(substring_matches)

    @classmethod
    def get_pixmap(
        cls,
        name: str,
        color: str = "#FFFFFF",
        size: int = 24,
        async_load: bool = False
    ) -> Optional[QPixmap]:
        """
        Returns a colored QPixmap of an icon.
        If async_load=True, loads in background and emits `icon_loaded(name, pixmap)` when done.
        """
        if not cls._icon_list:
            cls.list_icons()

        name_list = cls.search_icons(name, cls._icon_list)
        if name_list:
            name = name_list[0]
        elif name not in cls._icon_list:
            raise FileNotFoundError(f"[IconManager] Icon not found: {name}")

        cache_key = f"{name}|{color.lower()}|{size}"

        # --- Cache lookup ---
        with cls._icon_lock:
            if cache_key in cls._icon_cache:
                return QPixmap(cls._icon_cache[cache_key])

        file_path = os.path.join(cls._images_path, f"{name}.svg")
        if not os.path.exists(file_path):
            print(f"[IconManager] Missing icon file: {file_path}")
            return QPixmap()

        if async_load:
            # Run background worker
            task = _IconLoadTask(name, color, size, file_path, cls._cache_result)
            cls._thread_pool.start(task)
            return None
        else:
            pixmap = cls._load_icon_pixmap(file_path, color, size)
            cls._cache_result(name, color, size, pixmap)
            return pixmap

    @classmethod
    def clear_cache(cls):
        with cls._icon_lock:
            cls._icon_cache.clear()

    @classmethod
    def list_icons(cls) -> List[str]:
        """Lists all SVG icons in the configured image path."""
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
        """Sets the path where SVG icons are stored and clears caches."""
        cls._images_path = path
        cls.clear_cache()
        cls.list_icons()

    @classmethod
    def get_images_path(cls) -> str:
        return cls._images_path

    @classmethod
    def preload_common_icons(cls, icon_names: List[str], color: str = "#FFFFFF", size: int = 24):
        """Preload a batch of icons asynchronously for performance."""
        for name in icon_names:
            cls.get_pixmap(name, color, size, async_load=True)

    # --------------------------
    # Internal helpers
    # --------------------------

    @classmethod
    def _cache_result(cls, name: str, color: str, size: int, pixmap: QPixmap):
        """Safely cache and emit signal when ready."""
        cache_key = f"{name}|{color.lower()}|{size}"
        with cls._icon_lock:
            cls._icon_cache[cache_key] = QPixmap(pixmap)

        # Emit signal from notifier instance
        cls._notifier.icon_loaded.emit(name, pixmap)

    @staticmethod
    def _load_icon_pixmap(file_path: str, color: str, size: int) -> QPixmap:
        """Render and colorize SVG icon."""
        svg_renderer = QSvgRenderer(file_path)
        base_pixmap = QPixmap(size, size)
        base_pixmap.fill(Qt.transparent)

        painter = QPainter(base_pixmap)
        svg_renderer.render(painter)
        painter.end()

        tinted = QPixmap(size, size)
        tinted.fill(Qt.transparent)

        painter.begin(tinted)
        painter.drawPixmap(0, 0, base_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), QColor(color))
        painter.end()

        return tinted
