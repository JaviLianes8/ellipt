"""Pin the 1.0.0 public surface: signatures, defaults, constants, value semantics."""

from __future__ import annotations

import copy
import dataclasses
import inspect
import pickle
import typing

import pytest

import ellipt

POS = inspect.Parameter.POSITIONAL_OR_KEYWORD
KW = inspect.Parameter.KEYWORD_ONLY
EMPTY = inspect.Parameter.empty

SIGNATURES: dict[str, list[tuple[str, inspect._ParameterKind, object]]] = {
    "truncate": [
        ("text", POS, EMPTY),
        ("limit", POS, EMPTY),
        ("where", KW, "end"),
        ("unit", KW, "chars"),
        ("marker", KW, "..."),
        ("words", KW, False),
        ("ambiguous", KW, 1),
    ],
    "shorten": [
        ("text", POS, EMPTY),
        ("width", POS, EMPTY),
        ("where", KW, "end"),
        ("marker", KW, "..."),
        ("width_aware", KW, False),
        ("unit", KW, None),
        ("words", KW, False),
        ("ambiguous", KW, 1),
    ],
    "shorten_path": [
        ("path", POS, EMPTY),
        ("limit", POS, EMPTY),
        ("unit", KW, "chars"),
        ("marker", KW, "..."),
        ("sep", KW, None),
        ("ambiguous", KW, 1),
    ],
    "measure": [("text", POS, EMPTY), ("unit", POS, "chars"), ("ambiguous", KW, 1)],
    "iter_graphemes": [("text", POS, EMPTY)],
}


@pytest.mark.parametrize("name", sorted(SIGNATURES))
def test_signatures_are_pinned(name: str) -> None:
    params = inspect.signature(getattr(ellipt, name)).parameters.values()
    assert [(p.name, p.kind, p.default) for p in params] == SIGNATURES[name]


def test_constants_have_their_documented_values() -> None:
    assert ellipt.ELLIPSIS == "\u2026"
    assert ellipt.UNITS == ("chars", "graphemes", "columns", "bytes")
    assert isinstance(ellipt.UNITS, tuple)
    assert ellipt.UNICODE_VERSION == "18.0.0"
    assert typing.get_args(ellipt.Unit) == ellipt.UNITS
    assert typing.get_args(ellipt.Where) == ("start", "middle", "end")


def test_truncation_fields_are_pinned_in_order() -> None:
    fields = [(f.name, f.type) for f in dataclasses.fields(ellipt.Truncation)]
    assert fields == [
        ("text", "str"),
        ("head", "str"),
        ("marker", "str"),
        ("tail", "str"),
        ("original", "str"),
        ("unit", "Unit"),
        ("limit", "int"),
        ("size", "int"),
    ]
    assert ellipt.Truncation.__dataclass_params__.frozen  # type: ignore[attr-defined]


def test_public_objects_report_the_package_as_their_module() -> None:
    for name in ("Truncation", "iter_graphemes", "measure", "shorten", "shorten_path", "truncate"):
        assert getattr(ellipt, name).__module__ == "ellipt", name
    for name in ("truncated", "removed", "removed_span"):
        assert getattr(ellipt.Truncation, name).fget.__module__ == "ellipt", name
    assert ellipt.Truncation.__str__.__module__ == "ellipt"


def test_a_truncation_pickles_without_naming_a_private_module() -> None:
    result = ellipt.truncate("abcdefgh", 5, where="middle", marker=ellipt.ELLIPSIS)
    for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
        data = pickle.dumps(result, protocol)
        assert b"ellipt._" not in data
        assert pickle.loads(data) == result
    assert copy.deepcopy(result) == result and copy.copy(result) == result


def test_a_truncation_is_hashable_and_compares_field_by_field() -> None:
    a = ellipt.truncate("abcdefgh", 5)
    b = ellipt.truncate("abcdefgh", 5)
    assert a == b and hash(a) == hash(b) and len({a, b}) == 1
    assert a != ellipt.truncate("abcdefgh", 6)
    assert a != ellipt.truncate("abcdefgh", 5, unit="graphemes")
    assert repr(a).startswith("Truncation(text='ab...', head='ab', marker='...'")


def test_the_result_types_are_plain() -> None:
    result = ellipt.truncate("abcdef", 4)
    assert type(result) is ellipt.Truncation
    assert type(ellipt.shorten("abcdef", 4)) is str
    assert type(ellipt.shorten_path("/a/b/c/d.txt", 9)) is str
    assert type(ellipt.measure("abc")) is int
    clusters = ellipt.iter_graphemes("ab")
    assert iter(clusters) is clusters and [type(c) for c in clusters] == [str, str]


def test_shorten_is_the_text_of_truncate() -> None:
    for where in ("start", "middle", "end"):
        for unit in ellipt.UNITS:
            for words in (False, True):
                text = "alpha beta \u4e16\u754c gamma e\u0301 delta"
                kwargs = {"where": where, "unit": unit, "words": words, "ambiguous": 2}
                expected = ellipt.truncate(text, 12, **kwargs).text  # type: ignore[arg-type]
                assert ellipt.shorten(text, 12, **kwargs) == expected  # type: ignore[arg-type]
