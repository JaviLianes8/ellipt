"""Middle truncation of file system paths that keeps the root and the file name."""

from __future__ import annotations

from ._checks import Unit, check_ambiguous, check_limit, check_str, check_unit, shown_str
from ._core import truncate
from ._graphemes import grapheme_ends
from ._measure import size_of


def _separators(path: str, chars: str) -> list[int]:
    """Indices of separators that sit on grapheme cluster boundaries on both sides."""
    bounds = {0, *grapheme_ends(path)}
    return [i for i, ch in enumerate(path) if ch in chars and i in bounds and i + 1 in bounds]


def _root_stop(stops: list[int]) -> int | None:
    """Index into ``stops`` of the separator that ends the root, or None for no root."""
    if stops[:2] != [0, 1]:
        return 0  # "/", "C:\", "~/" or the top directory of a relative path
    # \\host\share\ (or //host/share/) is one root; without a share there is none to keep.
    return 3 if len(stops) >= 4 else None


def _shorten_name(name: str, limit: int, unit: Unit, marker: str, ambiguous: int) -> str:
    """Shorten a file name in the middle of its stem, keeping the extension if it can."""
    dot = name.rfind(".")
    if name[:dot].lower().endswith(".tar"):  # keep .tar.gz, .tar.xz and friends together
        dot -= 4
    if 0 < dot < len(name) - 1 and dot in {0, *grapheme_ends(name)}:
        stem, ext = name[:dot], name[dot:]
        room = limit - size_of(ext, unit, ambiguous)
        if room > size_of(marker, unit, ambiguous):
            short = truncate(
                stem, room, where="middle", unit=unit, marker=marker, ambiguous=ambiguous
            )
            candidate = short.text + ext
            if size_of(candidate, unit, ambiguous) <= limit:
                return candidate
    return truncate(name, limit, where="middle", unit=unit, marker=marker, ambiguous=ambiguous).text


def shorten_path(
    path: str,
    limit: int,
    *,
    unit: Unit = "chars",
    marker: str = "...",
    sep: str | None = None,
    ambiguous: int = 1,
) -> str:
    r"""Shorten a path to at most ``limit`` by dropping whole directories from the middle.

    The first component (``/``, ``C:\``, ``~/``, ``\\server\share\`` or a relative
    top directory) and the file name are kept, and as many directories next to the file
    name as fit, like the middle truncation of macOS Finder and editor tab titles. When
    only ``marker/name`` fits the root goes too, and when even that is too long the file
    name alone is shown, shortened in the middle of its stem with the extension (``.gz``
    or a compound ``.tar.gz``) kept. ``sep`` is the separator; by default both ``/`` and
    ``\`` count. ``unit``, ``marker`` and ``ambiguous`` mean the same as in ``truncate``,
    and the result never exceeds ``limit`` in ``unit``.

    Every argument is checked first: a wrong type raises ``TypeError``; an empty marker
    (the result would read as a different, real path), a marker larger than ``limit``, a
    ``sep`` that is not one character and the errors of ``truncate`` raise ``ValueError``.

    >>> shorten_path("/home/me/projects/app/src/main.py", 24)
    '/.../app/src/main.py'
    >>> shorten_path(r"C:\Users\me\Documents\report.pdf", 27)
    'C:\\...\\Documents\\report.pdf'
    >>> shorten_path("photos/2026/an_extremely_long_holiday_name.jpeg", 20)
    'an_ext...y_name.jpeg'
    """
    path = check_str("path", path)
    limit = check_limit("limit", limit)
    unit = check_unit(unit)
    marker = check_str("marker", marker)
    chars = "/\\" if sep is None else check_str("sep", sep)
    if len(chars) != 1 and sep is not None:
        raise ValueError(f"sep must be a single character, not {shown_str(chars)}")
    ambiguous = check_ambiguous(ambiguous)
    if marker == "":
        raise ValueError("marker must not be empty: the result would look like a real path")
    marker_size = size_of(marker, unit, ambiguous)
    if marker_size > limit:
        raise ValueError(f"marker of size {marker_size} does not fit in limit {limit} ({unit})")
    if size_of(path, unit, ambiguous) <= limit:
        return path
    stops = _separators(path.rstrip(chars), chars)
    name_start = stops[-1] + 1 if stops else 0
    candidates: list[str] = []
    first = _root_stop(stops) if stops else None
    if first is not None and len(stops) > first + 1:
        head = path[: stops[first] + 1]
        candidates += [head + marker + path[i:] for i in stops[first + 1 :] if i > stops[first] + 1]
    if stops:
        candidates.append(marker + path[name_start - 1 :])
    for candidate in candidates:
        if size_of(candidate, unit, ambiguous) <= limit:
            return candidate
    name = path[name_start:]
    if size_of(name, unit, ambiguous) <= limit:
        return name
    return _shorten_name(name, limit, unit, marker, ambiguous)
