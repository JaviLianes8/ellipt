"""Truncate strings with an ellipsis at the start, middle or end."""

from __future__ import annotations

from ._core import Where, truncate
from ._measure import Unit

__all__ = ["Where", "shorten"]


def shorten(
    text: str,
    width: int,
    *,
    where: Where = "end",
    marker: str = "...",
    width_aware: bool = False,
    unit: Unit | None = None,
    words: bool = False,
    ambiguous: int = 1,
) -> str:
    """Return text clipped to width, with marker marking where it was cut.

    The result never exceeds width, measured in ``unit``: ``"chars"`` (code points, the
    default), ``"graphemes"``, ``"columns"`` (display cells) or ``"bytes"`` (UTF-8).
    ``width_aware=True`` is a shorthand for ``unit="columns"``. The marker counts inside
    the width, and the cut never splits a grapheme cluster. ``words=True`` cuts at
    whitespace when it can. Text that already fits is returned unchanged. A width that
    cannot even hold the marker, or an unknown position or unit, raises ValueError.
    Use ``truncate`` for a typed result that also says what was removed.

    >>> shorten("hello world", 8)
    'hello...'
    >>> shorten("/var/log/app/service.log", 16, where="middle")
    '/var/lo...ce.log'
    >>> shorten("\\u5e7f\\u5e7f\\u5e7fx", 5, marker="..", width_aware=True)
    '\u5e7f..'
    """
    if unit is None:
        unit = "columns" if width_aware else "chars"
    elif width_aware and unit != "columns":
        raise ValueError(f"width_aware=True conflicts with unit={unit!r}")
    result = truncate(
        text, width, where=where, unit=unit, marker=marker, words=words, ambiguous=ambiguous
    )
    return result.text
