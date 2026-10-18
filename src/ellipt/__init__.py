"""Truncate strings with an ellipsis at the start, middle or end.

Limits can count code points, grapheme clusters, terminal columns or UTF-8 bytes, and
the cut never splits a grapheme cluster (UAX #29, Unicode 18.0.0 tables embedded).

``ELLIPSIS`` is U+2026 HORIZONTAL ELLIPSIS, ``UNITS`` lists what a limit can count,
``UNICODE_VERSION`` names the Unicode data in use, and ``Unit`` and ``Where`` are the
``Literal`` types of the ``unit`` and ``where`` arguments:

>>> ELLIPSIS, len(ELLIPSIS), measure(ELLIPSIS, "bytes")
('…', 1, 3)
>>> UNITS
('chars', 'graphemes', 'columns', 'bytes')
>>> UNICODE_VERSION
'18.0.0'
>>> import typing
>>> typing.get_args(Unit) == UNITS, typing.get_args(Where)
(True, ('start', 'middle', 'end'))
"""

from ._checks import UNITS, Unit, Where
from ._core import ELLIPSIS, Truncation, truncate
from ._graphemes import iter_graphemes
from ._measure import measure
from ._path import shorten_path
from ._props import UNICODE_VERSION
from ._shorten import shorten

__version__ = "1.0.0"

# Public classes and functions show and pickle as ellipt.<name>, so nothing depends on
# the private module that defines them, and doctest finds their examples here.
for _public in (Truncation, iter_graphemes, measure, shorten, shorten_path, truncate):
    _public.__module__ = __name__
for _member in vars(Truncation).values():
    if callable(_member) and str(getattr(_member, "__module__", "")).startswith("ellipt._"):
        _member.__module__ = __name__
del _public, _member

__all__ = [
    "ELLIPSIS",
    "UNICODE_VERSION",
    "UNITS",
    "Truncation",
    "Unit",
    "Where",
    "iter_graphemes",
    "measure",
    "shorten",
    "shorten_path",
    "truncate",
]
