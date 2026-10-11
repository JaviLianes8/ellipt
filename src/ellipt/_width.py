"""Display width helpers for East Asian and combining characters."""

from __future__ import annotations

import unicodedata

_WIDE = frozenset({"W", "F"})


def char_width(char: str) -> int:
    """Return the terminal display width of a single character (0, 1 or 2)."""
    if unicodedata.combining(char):
        return 0
    return 2 if unicodedata.east_asian_width(char) in _WIDE else 1


def text_width(text: str) -> int:
    """Return the total display width of text."""
    return sum(char_width(char) for char in text)
