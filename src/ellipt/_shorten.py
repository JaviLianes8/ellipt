"""Truncate strings with an ellipsis at the start, middle or end."""

from __future__ import annotations

from ._checks import Unit, Where, check_flag, check_limit, check_unit
from ._core import truncate


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

    ``shorten(text, width, ...)`` is ``truncate(text, width, ...).text``: the same rules,
    the same checks, only the string. The result never exceeds width, measured in
    ``unit``: ``"chars"`` (code points, the default), ``"graphemes"``, ``"columns"``
    (display cells) or ``"bytes"`` (UTF-8). ``width_aware=True`` is a shorthand for
    ``unit="columns"`` kept from 0.1.0; combining it with another unit raises
    ``ValueError``. The marker counts inside the width, and the cut never splits a
    grapheme cluster. ``words=True`` cuts at whitespace when it can. Text that already
    fits is returned unchanged. A width that cannot hold the marker, a negative width or
    an unknown position or unit raises ``ValueError``, a wrong type ``TypeError``.

    >>> shorten("hello world", 8)
    'hello...'
    >>> shorten("/var/log/app/service.log", 16, where="middle")
    '/var/lo...ce.log'
    >>> shorten("\\u5e7f\\u5e7f\\u5e7fx", 5, marker="..", width_aware=True)
    '广..'
    """
    width = check_limit("width", width)
    if check_flag("width_aware", width_aware):
        if unit is not None and (chosen := check_unit(unit)) != "columns":
            raise ValueError(f"width_aware=True conflicts with unit={chosen!r}")
        unit = "columns"
    elif unit is None:
        unit = "chars"
    result = truncate(
        text, width, where=where, unit=unit, marker=marker, words=words, ambiguous=ambiguous
    )
    return result.text
