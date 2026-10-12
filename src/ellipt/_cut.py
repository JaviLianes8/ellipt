"""Choose which grapheme clusters to keep on each side of the cut.

Every function works on a list of cluster sizes and returns ``(left, right)``: keep the
first ``left`` clusters and the clusters from index ``right`` onwards. ``left <= right``
always holds, so the kept head and tail never overlap.
"""

from __future__ import annotations


def _take_left(sizes: list[int], budget: int, start: int, stop: int) -> tuple[int, int]:
    """Greedily extend a prefix from ``start`` up to ``stop``; return (end, used)."""
    used = 0
    end = start
    while end < stop and used + sizes[end] <= budget:
        used += sizes[end]
        end += 1
    return end, used


def _take_right(sizes: list[int], budget: int, stop: int) -> tuple[int, int]:
    """Greedily extend a suffix down to index ``stop``; return (start, used)."""
    used = 0
    start = len(sizes)
    while start > stop and used + sizes[start - 1] <= budget:
        used += sizes[start - 1]
        start -= 1
    return start, used


def cut(sizes: list[int], budget: int, where: str) -> tuple[int, int]:
    """Return ``(left, right)`` keeping at most ``budget`` in total size."""
    count = len(sizes)
    if where == "end":
        return _take_left(sizes, budget, 0, count)[0], count
    if where == "start":
        return 0, _take_right(sizes, budget, 0)[0]
    left, used_left = _take_left(sizes, budget - budget // 2, 0, count)
    right, used_right = _take_right(sizes, budget - used_left, left)
    # A wide cluster may have stopped the left side early: give it what is left over.
    left, _ = _take_left(sizes, budget - used_left - used_right, left, right)
    return left, right


def _space(clusters: list[str], index: int) -> bool:
    return 0 <= index < len(clusters) and clusters[index].isspace()


def words_left(clusters: list[str], left: int) -> int:
    """Move a head end back to a whitespace boundary and drop trailing whitespace.

    Returns ``left`` unchanged when the head is a single word with no space to back off
    to, so a hard cut is used instead of an empty head.
    """
    end = left
    if left < len(clusters) and not _space(clusters, left) and not _space(clusters, left - 1):
        while end > 0 and not _space(clusters, end - 1):
            end -= 1
    while end > 0 and _space(clusters, end - 1):
        end -= 1
    return end if end > 0 else left


def words_right(clusters: list[str], right: int) -> int:
    """Move a tail start forward to a whitespace boundary and drop leading whitespace."""
    count = len(clusters)
    start = right
    if right > 0 and not _space(clusters, right) and not _space(clusters, right - 1):
        while start < count and not _space(clusters, start):
            start += 1
    while start < count and _space(clusters, start):
        start += 1
    return start if start < count else right
