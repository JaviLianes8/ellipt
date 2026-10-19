"""The truncation engine and its typed result."""

from __future__ import annotations

from dataclasses import dataclass

from ._checks import (
    Unit,
    Where,
    check_ambiguous,
    check_flag,
    check_limit,
    check_str,
    check_unit,
    check_where,
)
from ._cut import cut
from ._measure import cluster_size, clusters, size_of

ELLIPSIS = "…"


@dataclass(frozen=True)
class Truncation:
    """The outcome of ``truncate``: the shortened text and how it was built.

    ``text == head + marker + tail`` always holds. ``head`` is a prefix and ``tail`` a
    suffix of ``original``, both ending on grapheme cluster boundaries. When the text
    already fit, ``head`` is the whole original and ``marker`` and ``tail`` are empty.
    ``size`` is the size of ``text`` in ``unit`` and never exceeds ``limit``. A
    ``Truncation`` is immutable, hashable and compares equal field by field.

    >>> r = truncate("hello world", 8)
    >>> r.text, r.head, r.marker, r.tail
    ('hello...', 'hello', '...', '')
    >>> r.original, r.unit, r.limit, r.size
    ('hello world', 'chars', 8, 8)
    >>> r.truncated, r.removed, r.removed_span, str(r)
    (True, ' world', (5, 11), 'hello...')
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
        """True when part of the original was removed.

        >>> truncate("abc", 5).truncated, truncate("abcdef", 5).truncated
        (False, True)
        """
        return len(self.head) + len(self.tail) < len(self.original)

    @property
    def removed_span(self) -> tuple[int, int]:
        """``(start, stop)`` code point indices of the removed part of ``original``.

        >>> truncate("abcdefghij", 7, where="middle").removed_span
        (2, 8)
        """
        return len(self.head), len(self.original) - len(self.tail)

    @property
    def removed(self) -> str:
        """The part of ``original`` that the marker replaces (empty when it fit).

        >>> truncate("abcdefghij", 7, where="start").removed
        'abcdef'
        """
        start, stop = self.removed_span
        return self.original[start:stop]

    def __str__(self) -> str:
        """The shortened text, so a ``Truncation`` can be printed or formatted directly.

        >>> f"[{truncate('abcdefgh', 5)}]"
        '[ab...]'
        """
        return self.text


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

    ``words=True`` moves each cut to whitespace and trims the whitespace next to the
    marker, unless a single word fills the budget, in which case the cut stays hard.
    Tabs and other controls are zero columns; expand tabs first if they matter.
    ``ambiguous`` (1 or 2) is the width of East Asian Ambiguous characters in columns.
    Text that already fits is returned whole.

    Every argument is checked before the text is looked at: a wrong type raises
    ``TypeError``; a negative ``limit``, an unknown ``where`` or ``unit``, an
    ``ambiguous`` other than 1 or 2 and a marker larger than ``limit`` raise
    ``ValueError``, even when the text would fit.

    >>> truncate("hello world", 8).text
    'hello...'
    >>> r = truncate("hello brave new world", 15, marker=ELLIPSIS, words=True)
    >>> r.text, r.removed
    ('hello brave…', ' new world')
    >>> truncate("Espa\\U0001f1ea\\U0001f1f8a!", 7, unit="chars", marker="..").text
    'Espa..'
    >>> truncate("hi", 2)
    Traceback (most recent call last):
    ValueError: marker of size 3 does not fit in limit 2 (chars)
    """
    text = check_str("text", text)
    limit = check_limit("limit", limit)
    where = check_where(where)
    unit = check_unit(unit)
    marker = check_str("marker", marker)
    words = check_flag("words", words)
    ambiguous = check_ambiguous(ambiguous)
    marker_size = size_of(marker, unit, ambiguous)
    if marker_size > limit:
        raise ValueError(f"marker of size {marker_size} does not fit in limit {limit} ({unit})")
    size = size_of(text, unit, ambiguous)
    if size <= limit:
        return Truncation(text, text, "", "", text, unit, limit, size)
    # Cluster boundaries depend only on what precedes them, so an end cut counted in
    # chars or bytes (every cluster at least 1) only needs the first limit + 1 code points.
    window = text[: limit + 1] if where == "end" and unit in ("chars", "bytes") else text
    parts = clusters(window)
    sizes = [cluster_size(c, unit, ambiguous) for c in parts]
    spaces = [c.isspace() for c in parts] if words else None
    for budget in range(limit - marker_size, -1, -1):
        left, right = cut(sizes, budget, where, spaces)
        head, tail = "".join(parts[:left]), "".join(parts[right:])
        result = head + marker + tail
        # A marker that joins a neighbouring cluster can change its size; re-measure.
        size = size_of(result, unit, ambiguous)
        if size <= limit:
            return Truncation(result, head, marker, tail, text, unit, limit, size)
    # At budget 0 the head and tail hold only zero-size clusters; if one still joins the
    # marker into a wider cluster, the marker alone is the answer.
    return Truncation(marker, "", marker, "", text, unit, limit, marker_size)
