"""
Design System and Theme Tokens for Terminal Profile
Directly implements authentic neofetch-style terminal typography, color classes, and themes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class TerminalTheme:
    bg: str
    text_base: str
    key_color: str
    value_color: str
    add_color: str
    del_color: str
    cc_color: str  # Dot leaders and comment separators


DARK_THEME = TerminalTheme(
    bg="#161b22",
    text_base="#c9d1d9",
    key_color="#ffa657",
    value_color="#a5d6ff",
    add_color="#3fb950",
    del_color="#f85149",
    cc_color="#616e7f",
)

LIGHT_THEME = TerminalTheme(
    bg="#ffffff",
    text_base="#24292f",
    key_color="#bc4c00",
    value_color="#0969da",
    add_color="#1a7f37",
    del_color="#cf222e",
    cc_color="#8c959f",
)

THEMES: Dict[str, TerminalTheme] = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
}


def get_theme(name: str) -> TerminalTheme:
    return THEMES.get(name.lower(), DARK_THEME)
