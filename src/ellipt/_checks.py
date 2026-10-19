"""Argument checks shared by the public functions, with short error messages."""

from __future__ import annotations

import operator
from typing import Literal, SupportsIndex, cast

Unit = Literal["chars", "graphemes", "columns", "bytes"]
Where = Literal["start", "middle", "end"]
UNITS: tuple[Unit, ...] = ("chars", "graphemes", "columns", "bytes")
WHERES: tuple[Where, ...] = ("start", "middle", "end")

# No message ever quotes more than this many characters of a value the caller passed.
SHOWN = 40
# Read through type's own descriptor so a metaclass cannot hand back something odd.
_TYPE_NAME = type.__dict__["__name__"]


def type_name(value: object) -> str:
    """The name of the real type of ``value``, cut to ``SHOWN`` characters."""
    name = str(_TYPE_NAME.__get__(type(value)))
    return name if len(name) <= SHOWN else name[:SHOWN] + "..."


def shown_str(text: str) -> str:
    """``repr`` of a plain string, cut to ``SHOWN`` characters."""
    return repr(text) if len(text) <= SHOWN else repr(text[:SHOWN]) + "..."


def shown_int(number: int) -> str:
    """A plain int in digits, or by its size when it is too long to print."""
    if number.bit_length() <= 64:
        return str(number)
    sign = "a negative" if number < 0 else "an"
    return f"{sign} integer of {number.bit_length()} bits"


def check_str(name: str, value: object) -> str:
    """Return ``value`` as a plain ``str``; a subclass cannot change how it is measured."""
    # type() rather than isinstance(): an object cannot pass by faking __class__.
    if not issubclass(type(value), str):
        raise TypeError(f"{name} must be str, not {type_name(value)}")
    return str.__str__(cast(str, value))


def check_int(name: str, value: object) -> int:
    """Return ``value`` as a plain ``int``: any integer type except ``bool``."""
    if type(value) is bool or getattr(type(value), "__index__", None) is None:
        raise TypeError(f"{name} must be int, not {type_name(value)}")
    return operator.index(cast(SupportsIndex, value))


def check_limit(name: str, value: object) -> int:
    """Return ``value`` as a non-negative plain ``int``."""
    number = check_int(name, value)
    if number < 0:
        raise ValueError(f"{name} must be non-negative, not {shown_int(number)}")
    return number


def check_flag(name: str, value: object) -> bool:
    """Return ``value`` after checking it is a ``bool``."""
    if type(value) is not bool:
        raise TypeError(f"{name} must be bool, not {type_name(value)}")
    return value is True


def check_unit(unit: object) -> Unit:
    """Return the canonical spelling of ``unit`` after checking it is a known unit."""
    text = check_str("unit", unit)
    for known in UNITS:
        if text == known:
            return known
    choices = ", ".join(map(repr, UNITS))
    raise ValueError(f"unit must be one of {choices}, not {shown_str(text)}")


def check_where(where: object) -> Where:
    """Return the canonical spelling of ``where`` after checking it is a known position."""
    text = check_str("where", where)
    for known in WHERES:
        if text == known:
            return known
    raise ValueError(f"where must be 'start', 'middle' or 'end', not {shown_str(text)}")


def check_ambiguous(ambiguous: object) -> int:
    """Return ``ambiguous`` as a plain ``int`` after checking it is 1 or 2."""
    number = check_int("ambiguous", ambiguous)
    if number not in (1, 2):
        raise ValueError(f"ambiguous must be 1 or 2, not {shown_int(number)}")
    return number
