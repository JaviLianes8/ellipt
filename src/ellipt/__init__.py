"""Truncate strings with an ellipsis at the start, middle or end.

Limits can count code points, grapheme clusters, terminal columns or UTF-8 bytes, and
the cut never splits a grapheme cluster (UAX #29, Unicode 18.0.0 tables embedded).
"""

from __future__ import annotations

from ._core import ELLIPSIS, Truncation, Where, truncate
from ._graphemes import iter_graphemes
from ._measure import UNITS, Unit, measure
from ._path import shorten_path
from ._props import UNICODE_VERSION
from ._shorten import shorten

__version__ = "0.2.0"

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
