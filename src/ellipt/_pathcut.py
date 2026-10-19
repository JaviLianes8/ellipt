"""Choose which directories of a path to drop, in time linear in the path's length."""

from __future__ import annotations

from collections.abc import Iterator

from ._checks import Unit
from ._graphemes import grapheme_ends
from ._measure import cluster_size, clusters, size_of
from ._props import EXT_PICT_BIT, GCB, INCB_SHIFT, prop

_INCB_EXTEND = 3


def separators(path: str, chars: str) -> list[int]:
    """Indices of separators that sit on grapheme cluster boundaries on both sides."""
    bounds = {0, *grapheme_ends(path)}
    return [i for i, ch in enumerate(path) if ch in chars and i in bounds and i + 1 in bounds]


def _root_stop(stops: list[int]) -> int | None:
    """Index into ``stops`` of the separator that ends the root, or None for no root."""
    if stops[:2] != [0, 1]:
        return 0  # "/", "C:\", "~/" or the top directory of a relative path
    # \\host\share\ (or //host/share/) is one root; without a share there is none to keep.
    return 3 if len(stops) >= 4 else None


def candidates(path: str, stops: list[int], marker: str) -> Iterator[tuple[str, int]]:
    """Yield ``(prefix, start)`` for each shortening ``prefix + path[start:]``, longest first.

    ``path[start]`` is always a separator: first the root and the marker followed by fewer
    and fewer directories, then the marker and the file name alone.
    """
    first = _root_stop(stops)
    if first is not None:
        head = path[: stops[first] + 1] + marker  # built once: the root can be long
        for start in stops[first + 1 :]:
            if start > stops[first] + 1:
                yield head, start
    yield marker, stops[-1]


def _suffix_sizes(path: str, unit: Unit, ambiguous: int) -> dict[int, int]:
    """The size of ``path[i:]`` in ``unit`` for every cluster boundary ``i`` of ``path``."""
    sizes = {len(path): 0}
    end = len(path)
    total = 0
    for part in reversed(clusters(path)):
        total += cluster_size(part, unit, ambiguous)
        end -= len(part)
        sizes[end] = total
    return sizes


def _resets(separator: str) -> bool:
    """True when no grapheme rule looks back across ``separator``.

    The clusters after such a separator are then the same whatever text precedes it, so
    the size of ``prefix + path[start:]`` is the size of ``prefix + separator`` plus the
    size of what follows the separator in the original path.
    """
    code = prop(ord(separator))
    if (code >> INCB_SHIFT) & 0x03 == _INCB_EXTEND:
        return False
    return bool(code & EXT_PICT_BIT) or code & 0x0F not in (GCB["Extend"], GCB["ZWJ"])


def first_fit(
    path: str, options: Iterator[tuple[str, int]], limit: int, unit: Unit, ambiguous: int
) -> str | None:
    """Return the first ``prefix + path[start:]`` that fits in ``limit``, or None."""
    after = _suffix_sizes(path, unit, ambiguous)
    # Keyed by the prefix object itself: it is the same string for every candidate of a
    # kind, so the key hashes once and no long prefix is copied per candidate.
    heads: dict[tuple[str, str], int] = {}
    exact = False
    for prefix, start in options:
        if not exact:
            key = (prefix, path[start])
            if key not in heads:
                resets = _resets(path[start])
                heads[key] = size_of(prefix + path[start], unit, ambiguous) if resets else -1
            if heads[key] < 0:
                exact = True  # a separator that grapheme rules see through: measure each one
            elif heads[key] + after[start + 1] > limit:
                continue
        text = prefix + path[start:]
        if size_of(text, unit, ambiguous) <= limit:
            return text
        exact = True  # never expected; measuring every later candidate stays correct
    return None
