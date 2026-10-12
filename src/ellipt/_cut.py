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


def cut(
    sizes: list[int], budget: int, where: str, spaces: list[bool] | None = None
) -> tuple[int, int]:
    """Return ``(left, right)`` keeping at most ``budget`` in total size.

    With ``spaces`` (one flag per cluster: is it whitespace) every cut is moved to a word
    boundary and the whitespace next to the marker is dropped. If a single word fills
    the whole budget, the hard cut is used instead of returning nothing.
    """
    count = len(sizes)
    if where == "end":
        left = _take_left(sizes, budget, 0, count)[0]
        return (snap_left(spaces, left, False) if spaces else left), count
    if where == "start":
        right = _take_right(sizes, budget, 0)[0]
        return 0, (snap_right(spaces, right, False) if spaces else right)
    left, used_left = _take_left(sizes, budget - budget // 2, 0, count)
    if spaces:
        left = snap_left(spaces, left, True)
        used_left = sum(sizes[:left])
    right, used_right = _take_right(sizes, budget - used_left, left)
    if spaces:
        right = snap_right(spaces, right, True)
        used_right = sum(sizes[right:])
    # A wide cluster or a word snap may have left budget unused: hand it back.
    more, _ = _take_left(sizes, budget - used_left - used_right, left, right)
    left = max(left, snap_left(spaces, more, True)) if spaces else more
    if spaces and left == 0 and right == count:
        return cut(sizes, budget, where)
    return left, right


def snap_left(spaces: list[bool], left: int, allow_empty: bool) -> int:
    """Move a head end back to a word boundary and drop the whitespace before it."""
    end = left
    if left < len(spaces) and left > 0 and not spaces[left] and not spaces[left - 1]:
        while end > 0 and not spaces[end - 1]:
            end -= 1
    while end > 0 and spaces[end - 1]:
        end -= 1
    return end if end > 0 or allow_empty else left


def snap_right(spaces: list[bool], right: int, allow_empty: bool) -> int:
    """Move a tail start forward to a word boundary and drop the whitespace after it."""
    count = len(spaces)
    start = right
    if 0 < right < count and not spaces[right] and not spaces[right - 1]:
        while start < count and not spaces[start]:
            start += 1
    while start < count and spaces[start]:
        start += 1
    return start if start < count or allow_empty else right
