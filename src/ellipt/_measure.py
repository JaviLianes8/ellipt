"""Units of measure for a limit and the cluster sizes they assign."""

from __future__ import annotations

from ._checks import Unit, check_ambiguous, check_str, check_unit
from ._graphemes import grapheme_ends
from ._width import cluster_width


def clusters(text: str) -> list[str]:
    """Split ``text`` into extended grapheme clusters (UAX #29)."""
    found: list[str] = []
    start = 0
    for end in grapheme_ends(text):
        found.append(text[start:end])
        start = end
    return found


def cluster_size(cluster: str, unit: Unit, ambiguous: int) -> int:
    """Size of one grapheme cluster in ``unit``."""
    if unit == "chars":
        return len(cluster)
    if unit == "graphemes":
        return 1
    if unit == "columns":
        return cluster_width(cluster, ambiguous)
    return len(cluster.encode("utf-8", "surrogatepass"))


def size_of(text: str, unit: Unit, ambiguous: int) -> int:
    """Size of ``text`` in ``unit`` without validating the arguments."""
    if unit == "chars":
        return len(text)
    if unit == "bytes":
        return len(text.encode("utf-8", "surrogatepass"))
    if unit == "graphemes":
        return sum(1 for _ in grapheme_ends(text))
    return sum(cluster_size(c, unit, ambiguous) for c in clusters(text))


def measure(text: str, unit: Unit = "chars", *, ambiguous: int = 1) -> int:
    """Return the size of ``text`` in ``unit``, the way ``truncate`` measures it.

    ``"chars"`` counts code points (``len``), ``"graphemes"`` counts extended grapheme
    clusters (UAX #29, what a reader sees as one character), ``"columns"`` counts
    terminal display cells (UAX #11 East Asian Width, emoji sequences as one wide
    glyph, East Asian Ambiguous characters as ``ambiguous`` cells) and ``"bytes"``
    counts UTF-8 bytes, a lone surrogate as three. A wrong type raises ``TypeError``;
    an unknown unit or an ``ambiguous`` other than 1 or 2 raises ``ValueError``.

    >>> flag = "\\U0001f1ea\\U0001f1f8"
    >>> [measure(flag, u) for u in ("chars", "graphemes", "columns", "bytes")]
    [2, 1, 2, 8]
    >>> measure("\\u2026", "bytes"), measure("...", "bytes")
    (3, 3)
    >>> measure("\\u00a1", "columns"), measure("\\u00a1", "columns", ambiguous=2)
    (1, 2)
    """
    text = check_str("text", text)
    return size_of(text, check_unit(unit), check_ambiguous(ambiguous))
