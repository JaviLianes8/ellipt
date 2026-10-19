"""Every argument is checked first, wrong types raise TypeError, messages stay short."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from ellipt import iter_graphemes, measure, shorten, shorten_path, truncate

HUGE = 100_000
LONGEST = 160  # no message may grow with the size of what the caller passed

Call = Callable[[], object]


class Index:
    """An integer type that is not int, like numpy.int64."""

    def __init__(self, value: int) -> None:
        self.value = value

    def __index__(self) -> int:
        return self.value


WRONG_TYPES: list[tuple[str, Call, str]] = [
    ("text", lambda: truncate(b"x", 3), "text must be str, not bytes"),  # type: ignore[arg-type]
    ("limit float", lambda: truncate("x", 3.0), "limit must be int, not float"),  # type: ignore[arg-type]
    ("limit bool", lambda: truncate("x", True), "limit must be int, not bool"),
    ("where", lambda: truncate("x", 3, where=None), "where must be str, not NoneType"),  # type: ignore[arg-type]
    ("unit", lambda: truncate("x", 3, unit=None), "unit must be str, not NoneType"),  # type: ignore[arg-type]
    ("marker", lambda: truncate("x", 3, marker=1), "marker must be str, not int"),  # type: ignore[arg-type]
    ("words", lambda: truncate("x", 3, words="no"), "words must be bool, not str"),  # type: ignore[arg-type]
    ("words int", lambda: truncate("x", 3, words=1), "words must be bool, not int"),  # type: ignore[arg-type]
    ("ambiguous", lambda: truncate("x", 3, ambiguous=2.0), "ambiguous must be int, not float"),  # type: ignore[arg-type]
    ("width", lambda: shorten("x", "3"), "width must be int, not str"),  # type: ignore[arg-type]
    ("width_aware", lambda: shorten("x", 3, width_aware=None), "width_aware must be bool"),  # type: ignore[arg-type]
    ("measure text", lambda: measure(None), "text must be str, not NoneType"),  # type: ignore[arg-type]
    ("measure unit", lambda: measure("x", 1), "unit must be str, not int"),  # type: ignore[arg-type]
    ("measure ambiguous", lambda: measure("¡", "columns", ambiguous=2.0), "ambiguous"),  # type: ignore[arg-type]
    ("path", lambda: shorten_path(None, 5), "path must be str, not NoneType"),  # type: ignore[arg-type]
    ("sep", lambda: shorten_path("a/b", 5, sep=b"/"), "sep must be str, not bytes"),  # type: ignore[arg-type]
    ("iter_graphemes", lambda: iter_graphemes(None), "text must be str, not NoneType"),  # type: ignore[arg-type]
]  # fmt: skip


@pytest.mark.parametrize(("label", "call", "message"), WRONG_TYPES, ids=[w[0] for w in WRONG_TYPES])
def test_wrong_types_raise_type_error_at_the_call(label: str, call: Call, message: str) -> None:
    with pytest.raises(TypeError) as raised:
        call()
    assert str(raised.value).startswith(message)


BAD_VALUES: list[tuple[str, Call, str]] = [
    ("where", lambda: truncate("x", 3, where="w" * HUGE), "where must be"),  # type: ignore[arg-type]
    ("unit", lambda: truncate("x", 3, unit="u" * HUGE), "unit must be one of"),  # type: ignore[arg-type]
    ("measure unit", lambda: measure("x", "u" * HUGE), "unit must be one of"),  # type: ignore[arg-type]
    ("sep", lambda: shorten_path("x", 5, sep="/" * HUGE), "sep must be a single character"),
    ("limit", lambda: truncate("x", -(10**5000)), "limit must be non-negative"),
    ("width", lambda: shorten("x", -(10**5000)), "width must be non-negative"),
    ("ambiguous", lambda: truncate("x", 3, ambiguous=10**5000), "ambiguous must be 1 or 2"),
    ("marker", lambda: truncate("x", 3, marker="m" * HUGE), "marker of size 100000"),
    ("path marker", lambda: shorten_path("x", 3, marker="m" * HUGE), "marker of size 100000"),
    ("shorten unit", lambda: shorten("x", 3, width_aware=True, unit="bytes"), "width_aware=True"),
]  # fmt: skip


@pytest.mark.parametrize(("label", "call", "message"), BAD_VALUES, ids=[b[0] for b in BAD_VALUES])
def test_bad_values_raise_short_value_errors(label: str, call: Call, message: str) -> None:
    with pytest.raises(ValueError) as raised:
        call()
    assert str(raised.value).startswith(message) and len(str(raised.value)) <= LONGEST


def test_an_unknown_value_is_quoted_and_cut_to_40_characters() -> None:
    with pytest.raises(ValueError) as raised:
        truncate("x", 3, where="t" * 41)  # type: ignore[arg-type]
    assert str(raised.value).endswith(repr("t" * 40) + "...")
    with pytest.raises(ValueError) as raised:
        truncate("x", 3, where="t" * 40)  # type: ignore[arg-type]
    assert str(raised.value).endswith(repr("t" * 40))


def test_a_huge_integer_is_described_by_its_size() -> None:
    with pytest.raises(ValueError, match=r"not a negative integer of 65 bits$"):
        truncate("x", -(2**64))
    with pytest.raises(ValueError, match=r"not -18446744073709551615$"):
        truncate("x", -(2**64) + 1)
    with pytest.raises(ValueError, match=r"not an integer of 66 bits$"):
        measure("x", ambiguous=2**65)


def test_a_long_type_name_is_cut() -> None:
    odd = type("T" * 100, (), {})()
    with pytest.raises(TypeError) as raised:
        truncate(odd, 3)
    assert str(raised.value) == "text must be str, not " + "T" * 40 + "..."


def test_every_argument_is_checked_even_when_the_text_fits() -> None:
    for call in (
        lambda: truncate("", 2),
        lambda: shorten("hi", 2),
        lambda: shorten_path("a", 2),
        lambda: truncate("", 5, where="top"),  # type: ignore[arg-type]
        lambda: truncate("", 5, ambiguous=0),
        lambda: shorten_path("a", 5, marker=""),
        lambda: shorten_path("a", 5, sep=""),
    ):
        with pytest.raises(ValueError):
            call()


def test_integer_types_other_than_int_and_bool_are_accepted() -> None:
    assert truncate("abcdef", Index(4)).limit == 4  # type: ignore[arg-type]
    assert type(truncate("abcdef", Index(4)).limit) is int  # type: ignore[arg-type]
    assert shorten("abcdef", Index(4)) == "a..."  # type: ignore[arg-type]
    assert measure("¡", "columns", ambiguous=Index(2)) == 2  # type: ignore[arg-type]
    assert shorten_path("/a/b/c/d.txt", Index(9)) == ".../d.txt"  # type: ignore[arg-type]


class Lying(str):
    """A str subclass whose methods lie about its contents."""

    def __len__(self) -> int:
        return 1

    def __str__(self) -> str:
        return "lie"

    def encode(self, *args: object, **kwargs: object) -> bytes:
        return b""


def test_a_str_subclass_is_measured_and_returned_as_a_plain_str() -> None:
    text = Lying("abcdef")
    assert measure(text) == 6 and measure(text, "bytes") == 6
    result = truncate(text, 4)
    assert result.text == "a..." and type(result.original) is str and result.original == "abcdef"
    assert type(truncate(text, 10).text) is str
    assert type(truncate("abcdef", 4, marker=Lying("~")).marker) is str
    assert type(truncate("abcdef", 4, where=Lying("start")).text) is str  # type: ignore[arg-type]
    assert [type(c) for c in iter_graphemes(text)] == [str] * 6
    assert type(shorten_path(Lying("/a/b/c/d.txt"), 9)) is str
