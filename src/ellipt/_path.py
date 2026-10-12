"""Middle truncation of file system paths that keeps the root and the file name."""

from __future__ import annotations

from ._core import truncate
from ._graphemes import grapheme_ends
from ._measure import Unit, check_unit, size_of
from ._width import check_ambiguous


def _separators(path: str, sep: str | None) -> list[int]:
    """Indices of separators that sit on grapheme cluster boundaries on both sides."""
    chars = "/\\" if sep is None else sep
    bounds = {0, *grapheme_ends(path)}
    return [i for i, ch in enumerate(path) if ch in chars and i in bounds and i + 1 in bounds]


def _shorten_name(name: str, limit: int, unit: Unit, marker: str, ambiguous: int) -> str:
    """Shorten a file name in the middle of its stem, keeping the extension if it can."""
    dot = name.rfind(".")
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

    The first component (``/``, ``C:\``,``~/`` or a relative top directory) and the
    file name are kept, and as many directories next to the file name as fit, like the
    middle truncation of macOS Finder and editor tab titles. When only ``marker/name``
    fits the root goes too, and when even that is too long the file name alone is shown,
    shortened in the middle of its stem with the extension kept. ``sep`` is the
    separator; by default both ``/`` and ``\`` count. ``unit``, ``marker`` and
    ``ambiguous`` mean the same as in ``truncate``, and the result never exceeds
    ``limit`` in ``unit``.

    >>> shorten_path("/home/me/projects/app/src/main.py", 24)
    '/.../app/src/main.py'
    >>> shorten_path(r"C:\Users\me\Documents\report.pdf", 27)
    'C:\\...\\Documents\\report.pdf'
    >>> shorten_path("photos/2026/an_extremely_long_holiday_name.jpeg", 20)
    'an_ext...y_name.jpeg'
    """
    result = truncate(path, limit, where="middle", unit=unit, marker=marker, ambiguous=ambiguous)
    if not result.truncated:
        return path
    unit = check_unit(unit)
    ambiguous = check_ambiguous(ambiguous)
    if sep is not None and len(sep) != 1:
        raise ValueError(f"sep must be a single character, not {sep!r}")
    stops = _separators(path.rstrip("/\\" if sep is None else sep), sep)
    name_start = stops[-1] + 1 if stops else 0
    candidates: list[str] = []
    if len(stops) > 1:
        head = path[: stops[0] + 1]
        candidates += [head + marker + path[i:] for i in stops[1:]]
    if stops:
        candidates.append(marker + path[name_start - 1 :])
    for candidate in candidates:
        if size_of(candidate, unit, ambiguous) <= limit:
            return candidate
    name = path[name_start:]
    if size_of(name, unit, ambiguous) <= limit:
        return name
    return _shorten_name(name, limit, unit, marker, ambiguous)
