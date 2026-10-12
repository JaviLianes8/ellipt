"""Units of measure for a limit and the cluster sizes they assign."""

from __future__ import annotations

from typing import Literal

from ._graphemes import grapheme_ends
from ._width import check_ambiguous, cluster_width

Unit = Literal["chars", "graphemes", "columns", "bytes"]
UNITS: tuple[Unit, ...] = ("chars", "graphemes", "columns", "bytes")


def check_unit(unit: str) -> Unit:
    """Return ``unit`` after checking it names a supported unit."""
    for known in UNITS:
        if unit == known:
            return known
    raise ValueError(f"unit must be one of {', '.join(map(repr, UNITS))}, not {unit!r}")


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
    return sum(cluster_size(c, unit, ambiguous) for c in clusters(text))


def measure(text: str, unit: Unit = "chars", *, ambiguous: int = 1) -> int:
    """Return the size of ``text`` in ``unit``, the way ``truncate`` measures it.

    ``"chars"`` counts code points (``len``), ``"graphemes"`` counts extended grapheme
    clusters (UAX #29, what a reader sees as one character), ``"columns"`` counts
    terminal display cells (UAX #11 East Asian Width, emoji sequences as one wide
    glyph, East Asian Ambiguous characters as ``ambiguous`` cells) and ``"bytes"``
    counts UTF-8 bytes.

    >>> flag = "\\U0001f1ea\\U0001f1f8"
    >>> [measure(flag, u) for u in ("chars", "graphemes", "columns", "bytes")]
    [2, 1, 2, 8]
    >>> measure("\\u2026", "bytes"), measure("...", "bytes")
    (3, 3)
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be str, not {type(text).__name__}")
    return size_of(text, check_unit(unit), check_ambiguous(ambiguous))
