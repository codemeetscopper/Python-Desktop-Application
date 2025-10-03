# style_manager.py
from __future__ import annotations

import os
from typing import Dict, Optional, Union

import PySide6
from PySide6.QtCore import QByteArray
from PySide6.QtGui import QColor, QPalette, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

from common.appearance.iconmanager import IconManager

ColourLike = Union[str, QColor]


class StyleManager:
    """
    Singleton-style colour manager with a minimal API:
      - initialise(color_hex) -> bool
      - get_colour(colour_key, to_str=True) -> str | QColor
    It computes and stores:
      bg, bg1, bg2, fg, fg1, fg2,
      accent, accent_d1, accent_d2, accent_d3, accent_l1, accent_l2, accent_l3
    Notes:
      - Theme (light/dark) is inferred automatically from the current QApplication palette if present;
        otherwise defaults to 'light'.
      - Palette is generated internally and can be retrieved via get_palette() if needed.
    """

    # ---- Singleton state -----------------------------------------------------
    _initialised: bool = False
    _iconManager = IconManager()
    _colours: Dict[str, QColor] = {}
    _palette: Optional[QPalette] = None
    _resolved_mode: str = "light"  # "light" | "dark"

    # ---- Public API ----------------------------------------------------------
    @classmethod
    def initialise(
            cls,
            accent_hex: str,
            support_hex: str = "#FF9800",
            neutral_hex: str = "#4CAF50",
            theme: str = "light"
    ) -> bool:
        """
        Initialize the style manager with 3 base colors (accent, support, neutral).
        Each gets light/dark tiers (l1..l3, d1..d3).
        """
        try:
            # Convert to QColor (raises if invalid)
            accent = cls._to_qcolor(accent_hex)
            support = cls._to_qcolor(support_hex)
            neutral = cls._to_qcolor(neutral_hex)

            cls._resolved_mode = theme

            # Helpers
            white = QColor(255, 255, 255)
            black = QColor(0, 0, 0)
            lighten = lambda c, t: cls._blend(c, white, t)  # t in [0,1]
            darken = lambda c, t: cls._blend(c, black, t)  # t in [0,1]

            def make_tiers(base: QColor, name: str) -> dict:
                """Generate lighter/darker variants for a base colour."""
                return {
                    f"{name}": base,
                    f"{name}_l1": lighten(base, 0.15),
                    f"{name}_l2": lighten(base, 0.30),
                    f"{name}_l3": lighten(base, 0.45),
                    f"{name}_d1": darken(base, 0.15),
                    f"{name}_d2": darken(base, 0.30),
                    f"{name}_d3": darken(base, 0.45),
                }

            # Build colour dictionary
            colours = {}
            colours.update(make_tiers(accent, "accent"))
            colours.update(make_tiers(support, "support"))
            colours.update(make_tiers(neutral, "neutral"))

            # Background/Foreground based on theme
            if cls._resolved_mode == "dark":
                bg = QColor(18, 18, 18)  # #121212
                bg1 = lighten(bg, 0.08)
                bg2 = lighten(bg, 0.16)
                fg = QColor(237, 237, 237)  # light text
            else:
                bg = QColor(247, 247, 247)  # ~#F7F7F7
                bg1 = lighten(bg, 0.06)
                bg2 = lighten(bg, 0.12)
                fg = QColor(17, 17, 17)  # ~#111111

            fg1 = cls._blend(fg, bg, 0.35)
            fg2 = cls._blend(fg, bg, 0.60)

            colours.update({
                "bg": bg, "bg1": bg1, "bg2": bg2,
                "fg": fg, "fg1": fg1, "fg2": fg2,
            })

            # Save state
            cls._colours = colours
            cls._palette = cls._build_palette(colours)
            cls._initialised = True
            return True

        except Exception as ex:
            print(ex)
            return False
            cls._initialised = False
            cls._colours = {}
            cls._palette = None
            cls._resolved_mode = "light"
            return False

    @classmethod
    def get_colour(cls, colour_key: str, to_str: bool = True) -> Union[str, QColor]:
        """
        Return a named colour by key.
        - If to_str=True (default), returns '#RRGGBB'
        - If to_str=False, returns a QColor

        Valid keys:
            bg, bg1, bg2, fg, fg1, fg2,
            accent, accent_d1, accent_d2, accent_d3, accent_l1, accent_l2, accent_l3
        """
        if not cls._initialised:
            raise RuntimeError("StyleManager is not initialised. Call initialise('#RRGGBB') first.")
        key = colour_key.lower()
        if key not in cls._colours:
            raise KeyError(
                f"Unknown colour key '{colour_key}'. "
                f"Valid: {', '.join(sorted(cls._colours.keys()))}"
            )
        q = cls._colours[key]
        return cls.to_hex(q) if to_str else QColor(q)

    # (Optional) You can use this to apply to the app:
    @classmethod
    def get_palette(cls) -> QPalette:
        if not cls._initialised:
            raise RuntimeError("StyleManager is not initialised.")
        return cls._palette

    @classmethod
    def is_initialised(cls) -> bool:
        return cls._initialised

    @classmethod
    def get_pixmap(cls, image_name: str, color: str = "#FFFFFF", size: int = 15) -> QPixmap:
        return cls._iconManager.get_pixmap(image_name, color, size)

    @classmethod
    def mode(cls) -> str:
        """Returns the resolved theme mode: 'light' or 'dark'."""
        return cls._resolved_mode

    # ---- Internal helpers ----------------------------------------------------
    @classmethod
    def _auto_mode(cls) -> str:
        """Infer light/dark from QApplication's current palette; fallback to light."""
        app = QApplication.instance()
        if app is not None:
            bg = app.palette().color(QPalette.Window)
            return "dark" if cls._relative_luminance(bg) < 0.25 else "light"
        return "light"

    @staticmethod
    def _to_qcolor(value: ColourLike) -> QColor:
        if isinstance(value, QColor):
            q = QColor(value)
        elif isinstance(value, str):
            q = QColor()
            q.setNamedColor(value)
        else:
            raise TypeError("Color must be a hex string like '#RRGGBB' or a QColor.")
        if not q.isValid():
            raise ValueError(f"Invalid color string: {value!r}")
        return q

    @staticmethod
    def to_hex(c: ColourLike) -> str:
        q = StyleManager._to_qcolor(c)
        return "#{:02X}{:02X}{:02X}".format(q.red(), q.green(), q.blue())

    # --- Colour math (linear sRGB for better blending) -----------------------
    @staticmethod
    def _srgb_to_linear(c: float) -> float:
        c = c / 255.0
        if c <= 0.04045:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    @staticmethod
    def _linear_to_srgb(c: float) -> float:
        if c <= 0.0031308:
            v = c * 12.92
        else:
            v = 1.055 * (c ** (1 / 2.4)) - 0.055
        return max(0, min(1, v)) * 255.0

    @classmethod
    def _blend(cls, c1: QColor, c2: QColor, t: float) -> QColor:
        """Blend c1 -> c2 by factor t in linear RGB."""
        t = max(0.0, min(1.0, t))
        r1, g1, b1, a1 = c1.red(), c1.green(), c1.blue(), c1.alpha()
        r2, g2, b2, a2 = c2.red(), c2.green(), c2.blue(), c2.alpha()
        # linearize
        lr1, lg1, lb1 = map(cls._srgb_to_linear, (r1, g1, b1))
        lr2, lg2, lb2 = map(cls._srgb_to_linear, (r2, g2, b2))
        # mix
        lr = lr1 * (1 - t) + lr2 * t
        lg = lg1 * (1 - t) + lg2 * t
        lb = lb1 * (1 - t) + lb2 * t
        la = a1 * (1 - t) + a2 * t
        # gamma back
        rr = int(round(cls._linear_to_srgb(lr)))
        gg = int(round(cls._linear_to_srgb(lg)))
        bb = int(round(cls._linear_to_srgb(lb)))
        aa = int(round(max(0, min(255, la))))
        q = QColor(rr, gg, bb)
        q.setAlpha(aa)
        return q

    @staticmethod
    def _relative_luminance(c: QColor) -> float:
        r = StyleManager._srgb_to_linear(c.red())
        g = StyleManager._srgb_to_linear(c.green())
        b = StyleManager._srgb_to_linear(c.blue())
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    @classmethod
    def _build_palette(cls, colours: Dict[str, QColor]) -> QPalette:
        """Create a richly styled QPalette from computed colours."""
        p = QPalette()

        bg = colours["bg"]
        bg_alt = colours["bg1"]
        fg = colours["fg"]
        fg_alt = colours["fg1"]
        fg_muted = colours["fg2"]
        accent = colours["accent"]

        # Accent variations
        accent_l1 = colours["accent_l1"]
        accent_l2 = colours["accent_l2"]
        accent_d1 = colours["accent_d1"]
        accent_d2 = colours["accent_d2"]

        # Base surfaces
        p.setColor(QPalette.Window, bg)
        p.setColor(QPalette.Base, bg)
        p.setColor(QPalette.AlternateBase, bg_alt)
        p.setColor(QPalette.Button, bg_alt)
        p.setColor(QPalette.ToolTipBase, bg_alt)
        p.setColor(QPalette.ToolTipText, fg)

        # Text
        p.setColor(QPalette.WindowText, fg)
        p.setColor(QPalette.Text, fg)
        p.setColor(QPalette.ButtonText, fg)
        p.setColor(QPalette.PlaceholderText, fg_alt)

        # Links & selections
        p.setColor(QPalette.Link, accent_l1)
        p.setColor(QPalette.LinkVisited, cls._blend(accent_d1, fg_muted, 0.3))
        p.setColor(QPalette.Highlight, accent)
        p.setColor(QPalette.HighlightedText, cls._best_contrast(accent, fg, QColor(255, 255, 255)))

        # Shadows and borders
        p.setColor(QPalette.Shadow, accent_d2)
        p.setColor(QPalette.Light, accent_l2)
        p.setColor(QPalette.Midlight, accent_l1)
        p.setColor(QPalette.Dark, accent_d2)
        p.setColor(QPalette.Mid, accent_d1)

        # Disabled state
        disabled_fg = cls._blend(fg_muted, bg, 0.5)
        disabled_bg = cls._blend(bg, bg_alt, 0.3)
        for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText, QPalette.ToolTipText,
                     QPalette.PlaceholderText):
            p.setColor(QPalette.Disabled, role, disabled_fg)
        for role in (QPalette.Window, QPalette.Base, QPalette.Button):
            p.setColor(QPalette.Disabled, role, disabled_bg)
        p.setColor(QPalette.Disabled, QPalette.Highlight, cls._blend(accent, bg, 0.5))
        p.setColor(QPalette.Disabled, QPalette.HighlightedText, disabled_fg)

        return p

    @classmethod
    def _best_contrast(cls, bg: QColor, *candidates: QColor) -> QColor:
        """Return the color with best contrast against the background."""
        def contrast(c: QColor) -> float:
            return abs(cls._relative_luminance(bg) - cls._relative_luminance(c))
        return max(candidates, key=contrast)
