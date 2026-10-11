"""Truncate strings with an ellipsis at the start, middle or end."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from ._width import char_width, text_width

Where = Literal["start", "middle", "end"]


def _unit_width(char: str) -> int:
    return 1


def _take_left(text: str, budget: int, measure: Callable[[str], int]) -> str:
    used = 0
    kept: list[str] = []
    for char in text:
        width = measure(char)
        if used + width > budget:
            break
        used += width
        kept.append(char)
    return "".join(kept)


def _take_right(text: str, budget: int, measure: Callable[[str], int]) -> str:
    used = 0
    kept: list[str] = []
    for char in reversed(text):
        width = measure(char)
        if used + width > budget:
            break
        used += width
        kept.append(char)
    return "".join(reversed(kept))


def shorten(
    text: str,
    width: int,
    *,
    where: Where = "end",
    marker: str = "...",
    width_aware: bool = False,
) -> str:
    """Return text clipped to width, with marker marking where it was cut.

    The result never exceeds width. When width_aware is set, width is measured
    in display columns (wide characters count as two) instead of code points.
    Text that already fits is returned unchanged. A width that cannot even hold
    the marker, or an unknown position, raises ValueError.
    """
    if where not in ("start", "middle", "end"):
        raise ValueError(f"where must be 'start', 'middle' or 'end', not {where!r}")
    if width < 0:
        raise ValueError(f"width must be non-negative, not {width}")

    measure = char_width if width_aware else _unit_width
    size = text_width(text) if width_aware else len(text)
    if size <= width:
        return text

    marker_size = text_width(marker) if width_aware else len(marker)
    if marker_size > width:
        raise ValueError(f"marker of width {marker_size} does not fit in width {width}")
    budget = width - marker_size

    if where == "end":
        return _take_left(text, budget, measure) + marker
    if where == "start":
        return marker + _take_right(text, budget, measure)
    left = budget - budget // 2
    right = budget // 2
    return _take_left(text, left, measure) + marker + _take_right(text, right, measure)
