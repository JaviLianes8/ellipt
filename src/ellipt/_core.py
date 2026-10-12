"""The truncation engine and its typed result."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ._cut import cut, words_left, words_right
from ._measure import Unit, check_unit, cluster_size, clusters, size_of
from ._width import check_ambiguous

Where = Literal["start", "middle", "end"]
ELLIPSIS = "\u2026"


@dataclass(frozen=True)
class Truncation:
    """The outcome of ``truncate``: the shortened text and how it was built.

    ``text == head + marker + tail`` always holds. ``head`` is a prefix and ``tail`` a
    suffix of ``original``, both ending on grapheme cluster boundaries. When the text
    already fit, ``head`` is the whole original and ``marker`` and ``tail`` are empty.
    ``size`` is the size of ``text`` in ``unit`` and never exceeds ``limit``.
    """

    text: str
    head: str
    marker: str
    tail: str
    original: str
    unit: Unit
    limit: int
    size: int

    @property
    def truncated(self) -> bool:
        """True when part of the original was removed."""
        return len(self.head) + len(self.tail) < len(self.original)

    @property
    def removed_span(self) -> tuple[int, int]:
        """``(start, stop)`` code point indices of the removed part of ``original``."""
        return len(self.head), len(self.original) - len(self.tail)

    @property
    def removed(self) -> str:
        """The part of ``original`` that the marker replaces (empty when it fit)."""
        start, stop = self.removed_span
        return self.original[start:stop]

    def __str__(self) -> str:
        return self.text


def _check(text: str, limit: int, where: str, marker: str) -> None:
    if not isinstance(text, str):
        raise TypeError(f"text must be str, not {type(text).__name__}")
    if not isinstance(marker, str):
        raise TypeError(f"marker must be str, not {type(marker).__name__}")
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise TypeError(f"limit must be int, not {type(limit).__name__}")
    if where not in ("start", "middle", "end"):
        raise ValueError(f"where must be 'start', 'middle' or 'end', not {where!r}")
    if limit < 0:
        raise ValueError(f"width must be non-negative, not {limit}")


def truncate(
    text: str,
    limit: int,
    *,
    where: Where = "end",
    unit: Unit = "chars",
    marker: str = "...",
    words: bool = False,
    ambiguous: int = 1,
) -> Truncation:
    """Shorten ``text`` to at most ``limit`` and report exactly what happened.

    ``where`` puts the marker at the ``"end"`` (like CSS ``text-overflow: ellipsis``),
    the ``"start"`` (keep the tail, for ids and log lines) or the ``"middle"`` (keep
    both ends, for paths and hashes). ``unit`` is what ``limit`` counts: ``"chars"``
    (code points), ``"graphemes"``, ``"columns"`` (terminal cells) or ``"bytes"``
    (UTF-8); see ``measure``. The marker is measured in the same unit and counted inside
    the limit. The cut always falls on an extended grapheme cluster boundary (UAX #29),
    so accents, flags and emoji ZWJ sequences are kept whole or dropped whole.

    ``words=True`` moves the cut back to whitespace and trims the whitespace next to the
    marker, unless a single word fills the budget, in which case the cut stays hard.
    ``ambiguous`` (1 or 2) is the width of East Asian Ambiguous characters in columns.

    Text that already fits is returned whole. A marker larger than ``limit``, a negative
    limit or an unknown ``where`` or ``unit`` raises ``ValueError``.

    >>> truncate("hello world", 8).text
    'hello...'
    >>> r = truncate("hello brave new world", 15, marker=ELLIPSIS, words=True)
    >>> r.text, r.removed
    ('hello brave\u2026', ' new world')
    >>> truncate("Espa\\U0001f1ea\\U0001f1f8a!", 7, unit="chars", marker="..").text
    'Espa..'
    """
    _check(text, limit, where, marker)
    unit = check_unit(unit)
    ambiguous = check_ambiguous(ambiguous)
    size = size_of(text, unit, ambiguous)
    if size <= limit:
        return Truncation(text, text, "", "", text, unit, limit, size)
    marker_size = size_of(marker, unit, ambiguous)
    if marker_size > limit:
        raise ValueError(f"marker of width {marker_size} does not fit in width {limit}")
    parts = clusters(text)
    sizes = [cluster_size(c, unit, ambiguous) for c in parts]
    for budget in range(limit - marker_size, -1, -1):
        left, right = cut(sizes, budget, where)
        if words:
            left = words_left(parts, left) if where != "start" else left
            right = words_right(parts, right) if where != "end" else right
        head, tail = "".join(parts[:left]), "".join(parts[right:])
        result = head + marker + tail
        # A marker that joins a neighbouring cluster can change its size; re-measure.
        size = size_of(result, unit, ambiguous)
        if size <= limit:
            return Truncation(result, head, marker, tail, text, unit, limit, size)
    return Truncation(marker, "", marker, "", text, unit, limit, marker_size)
