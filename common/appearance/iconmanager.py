import os
import threading
import re
from typing import Dict, List, Optional
from PySide6.QtCore import QObject, Signal, Qt, QThreadPool, QRunnable
from PySide6.QtGui import QPixmap, QPainter, QColor, QImage
from PySide6.QtSvg import QSvgRenderer


# ------------------------------
# Internal async worker
# ------------------------------
class _IconLoadTask(QRunnable):
    """Background worker for loading and caching icons as QImage."""
    def __init__(self, name: str, color: str, size: int, file_path: str, callback):
        super().__init__()
        self.name = name
        self.color = color
        self.size = size
        self.file_path = file_path
        self.callback = callback

    def run(self):
        # Render to a thread-safe QImage in the background
        image = IconManager._load_icon_image(self.file_path, self.color, self.size)
        if self.callback:
            # The callback will receive the QImage object
            self.callback(self.name, self.color, self.size, image)


# ------------------------------
# Internal notifier QObject
# ------------------------------
class _IconNotifier(QObject):
    """QObject wrapper so static IconManager can still emit Qt signals."""
    # Emit a generic object to safely pass QImage across threads
    icon_loaded = Signal(str, object)


# ------------------------------
# Main IconManager class
# ------------------------------
class IconManager:
    """Thread-safe, cached and async-capable SVG icon manager (static API)."""

    # Internal state
    _icon_cache: Dict[str, QImage] = {}  # Cache QImage, not QPixmap
    _svg_cache: Dict[str, str] = {}      # Cache generated SVG strings
    _icon_lock = threading.Lock()
    _images_path: str = r"../../resources/images/meterialicons/"
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

        exact_matches, exact_core_matches, core_matches, substring_matches = [], [], [], []
        all_suffixes = IconManager._style_suffixes + IconManager._size_suffixes

        for icon in icons:
            icon_lower = icon.lower()
            if query_lower == icon_lower:
                exact_matches.append(icon)
                continue

            # Iteratively strip all known suffixes to find the true core name
            core_name = icon_lower
            stripped = True
            while stripped:
                stripped = False
                for suffix in all_suffixes:
                    if core_name.endswith(suffix):
                        core_name = core_name[: -len(suffix)]
                        stripped = True
                        break  # Restart the inner loop to handle multiple suffixes

            if query_lower == core_name:
                exact_core_matches.append(icon)
            elif query_lower in core_name:
                core_matches.append(icon)
            elif query_lower in icon_lower:
                substring_matches.append(icon)

        return sorted(exact_matches) + sorted(exact_core_matches) + sorted(core_matches) + sorted(substring_matches)

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
        If async_load=True, loads in background and emits `icon_loaded(name, image)` when done.
        """
        if not cls._icon_list:
            cls.list_icons()

        # Find the full icon name if a partial name is given
        name_list = cls.search_icons(name, cls._icon_list)
        if name_list:
            resolved_name = name_list[0]
        elif name in cls._icon_list:
            resolved_name = name
        else:
            raise FileNotFoundError(f"[IconManager] Icon not found: {name}")

        cache_key = f"{resolved_name}|{color.lower()}|{size}"

        # --- Cache lookup (now checking for QImage) ---
        with cls._icon_lock:
            if cache_key in cls._icon_cache:
                cached_image = cls._icon_cache[cache_key]
                if async_load:
                    # For async, emit signal immediately with cached data instead of returning
                    cls._notifier.icon_loaded.emit(resolved_name, cached_image)
                    return None
                else:
                    # For sync, convert cached QImage to QPixmap and return
                    return QPixmap.fromImage(cached_image)

        file_path = os.path.join(cls._images_path, f"{resolved_name}.svg")
        if not os.path.exists(file_path):
            print(f"[IconManager] Missing icon file: {file_path}")
            return QPixmap()

        if async_load:
            # Run background worker to produce a QImage
            task = _IconLoadTask(resolved_name, color, size, file_path, cls._cache_result)
            cls._thread_pool.start(task)
            return None  # Return immediately for async calls
        else:
            # Synchronous path: render QImage, cache it, and return a QPixmap
            image = cls._load_icon_image(file_path, color, size)
            cls._cache_result(resolved_name, color, size, image)
            return QPixmap.fromImage(image)

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
    def _cache_result(cls, name: str, color: str, size: int, image: QImage):
        """Safely cache the QImage and emit the signal."""
        if not image or image.isNull():
            return

        cache_key = f"{name}|{color.lower()}|{size}"
        with cls._icon_lock:
            # Store a copy of the QImage in the cache
            cls._icon_cache[cache_key] = QImage(image)

        # Emit signal from notifier instance with the QImage object
        cls._notifier.icon_loaded.emit(name, image)

    @staticmethod
    def _load_icon_image(file_path: str, color: str, size: int) -> QImage:
        """Render and colorize SVG icon into a QImage (thread-safe)."""
        svg_renderer = QSvgRenderer(file_path)
        # Create a QImage, which is safe to use in non-GUI threads
        image = QImage(size, size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)

        painter = QPainter(image)
        svg_renderer.render(painter)
        # Apply color tint
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(image.rect(), QColor(color))
        painter.end()

        return image

    @staticmethod
    def _load_icon_pixmap(file_path: str, color: str, size: int) -> QPixmap:
        """DEPRECATED: This method is unsafe in threads. Use _load_icon_image."""
        return QPixmap.fromImage(IconManager._load_icon_image(file_path, color, size))

    # --------------------------
    # New: SVG-string loader (sync / async)
    # --------------------------
    class _SvgLoadTask(QRunnable):
        """Background worker that produces a colorized SVG string."""
        def __init__(self, name: str, color: str, size: int, file_path: str, callback):
            super().__init__()
            self.name = name
            self.color = color
            self.size = size
            self.file_path = file_path
            self.callback = callback

        def run(self):
            svg_text = IconManager._load_svg_text(self.file_path, self.color, self.size)
            if self.callback:
                self.callback(self.name, self.color, self.size, svg_text)

    @classmethod
    def get_svg_data(
        cls,
        name: str,
        color: str = "#FFFFFF",
        size: int = 24,
        async_load: bool = False
    ) -> Optional[str]:
        """
        Return SVG source (text) for an icon, colorized and sized.
        If async_load=True, this returns None immediately and will emit
        _notifier.icon_loaded(name, svg_text) when ready.
        """
        if not cls._icon_list:
            cls.list_icons()

        # Resolve name similar to get_pixmap
        name_list = cls.search_icons(name, cls._icon_list)
        if name_list:
            resolved_name = name_list[0]
        elif name in cls._icon_list:
            resolved_name = name
        else:
            raise FileNotFoundError(f"[IconManager] Icon not found: {name}")

        cache_key = f"{resolved_name}|{color.lower()}|{size}"

        # Check SVG cache
        with cls._icon_lock:
            if cache_key in cls._svg_cache:
                cached_svg = cls._svg_cache[cache_key]
                if async_load:
                    # emit cached result asynchronously (signal carries object)
                    cls._notifier.icon_loaded.emit(resolved_name, cached_svg)
                    return None
                else:
                    return cached_svg

        file_path = os.path.join(cls._images_path, f"{resolved_name}.svg")
        if not os.path.exists(file_path):
            print(f"[IconManager] Missing icon file: {file_path}")
            return ""

        if async_load:
            task = cls._SvgLoadTask(resolved_name, color, size, file_path, cls._cache_svg_result_svg)
            cls._thread_pool.start(task)
            return None
        else:
            svg_text = cls._load_svg_text(file_path, color, size)
            cls._cache_svg_result_svg(resolved_name, color, size, svg_text)
            return svg_text

    @classmethod
    def _cache_svg_result_svg(cls, name: str, color: str, size: int, svg_text: str):
        """Cache generated svg string and emit through notifier."""
        if not svg_text:
            return
        cache_key = f"{name}|{color.lower()}|{size}"
        with cls._icon_lock:
            cls._svg_cache[cache_key] = svg_text
        # Emit the svg text as the second argument (object)
        cls._notifier.icon_loaded.emit(name, svg_text)

    @staticmethod
    def _load_svg_text(file_path: str, color: str, size: int) -> str:
        """
        Read SVG file, inject a small <style> to apply a color and set width/height.
        Returns modified SVG text (safe to write to temp or use as string).
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                svg = f.read()
        except Exception as e:
            print(f"[IconManager] Failed to read SVG {file_path}: {e}")
            return ""

        # Find the opening <svg ...> tag
        m = re.search(r'<svg\b[^>]*>', svg, flags=re.IGNORECASE)
        if not m:
            return svg  # not an SVG? return as-is

        svg_open = m.group(0)
        insert_pos = m.end()

        # Ensure color is a hex or valid CSS color string
        color_str = color if color else "#000000"

        # Create a conservative style that targets common shape elements
        style_tag = (
            f"<style>"
            f"path, circle, rect, polygon, ellipse, line, polyline {{ fill: {color_str}; stroke: {color_str}; }}"
            f"</style>"
        )

        # Avoid inserting duplicate identical style (simple check)
        if style_tag not in svg:
            svg = svg[:insert_pos] + style_tag + svg[insert_pos:]

        # Update width/height attributes in the svg_open tag (if present) or add them
        def replace_attr(tag: str, attr: str, val: int) -> str:
            if re.search(rf'\b{attr}\s*=', tag, flags=re.IGNORECASE):
                return re.sub(rf'({attr}\s*=\s*)(["\'])(.*?)\2', rf'\1"\{val}\\"', tag)
            else:
                return tag[:-1] + f' {attr}="{val}">'

        # Simple approach: replace width and height attrs if present, else add them
        new_open = svg_open
        if re.search(r'\bwidth\s*=', svg_open, flags=re.IGNORECASE):
            new_open = re.sub(r'(width\s*=\s*)(["\'])(.*?)\2', rf'\1"{size}"', new_open)
        else:
            new_open = new_open[:-1] + f' width="{size}"' + '>'

        if re.search(r'\bheight\s*=', new_open, flags=re.IGNORECASE):
            new_open = re.sub(r'(height\s*=\s*)(["\'])(.*?)\2', rf'\1"{size}"', new_open)
        else:
            # if height not present, add it before the closing '>'
            if new_open.endswith('>'):
                new_open = new_open[:-1] + f' height="{size}">'

        # Replace only the first occurrence of the original open tag
        svg = svg.replace(svg_open, new_open, 1)

        return svg

