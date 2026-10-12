import dataclasses
import importlib.resources
import inspect

import pytest

import ellipt

# The public API. Add every exported name here as the library grows; this list is the
# contract and the test below fails if the module and this list disagree.
PUBLIC_API: list[str] = [
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


def test_all_lists_exactly_the_public_api() -> None:
    assert sorted(ellipt.__all__) == sorted(PUBLIC_API)


def test_every_exported_name_resolves() -> None:
    for name in ellipt.__all__:
        assert hasattr(ellipt, name)


def test_version_is_a_three_part_string() -> None:
    parts = ellipt.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_the_package_ships_type_information() -> None:
    assert importlib.resources.files("ellipt").joinpath("py.typed").is_file()


def test_the_0_1_0_signature_of_shorten_is_kept() -> None:
    params = list(inspect.signature(ellipt.shorten).parameters.values())
    assert [p.name for p in params[:5]] == ["text", "width", "where", "marker", "width_aware"]
    assert [p.kind for p in params[:2]] == [inspect.Parameter.POSITIONAL_OR_KEYWORD] * 2
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in params[2:])
    assert (params[2].default, params[3].default, params[4].default) == ("end", "...", False)


def test_truncation_is_an_immutable_value() -> None:
    result = ellipt.truncate("abcdef", 4)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.text = "x"  # type: ignore[misc]
    assert result == ellipt.truncate("abcdef", 4)


SAMPLES = [
    "",
    "plain ascii text that is long",
    "caf\u00e9 cre\u0300me br\u00fbl\u00e9e",
    "\U0001f468\u200d\U0001f469\u200d\U0001f467 family \U0001f1ea\U0001f1f8 flag",
    "\u4f60\u597d\uff0c\u4e16\u754c\u3002\u65e5\u672c\u8a9e\u306e\u6587",
    "\u1100\u1161\u11a8\uac00 \u0915\u094d\u0937 line\r\nbreak",
]


@pytest.mark.parametrize("text", SAMPLES)
def test_the_whole_promise_holds_for_every_unit_position_and_limit(text: str) -> None:
    for unit in ellipt.UNITS:
        full = ellipt.measure(text, unit)
        bounds = {0} | {sum(map(len, c)) for c in _prefixes(text)}
        for where in ("start", "middle", "end"):
            for marker in ("...", ellipt.ELLIPSIS, ""):
                for limit in range(ellipt.measure(marker, unit), full + 2):
                    r = ellipt.truncate(text, limit, where=where, unit=unit, marker=marker)
                    assert r.size == ellipt.measure(r.text, unit) <= limit
                    assert r.text == r.head + r.marker + r.tail
                    assert text.startswith(r.head) and text.endswith(r.tail)
                    assert len(r.head) in bounds and len(text) - len(r.tail) in bounds
                    assert r.truncated is (full > limit)
                    assert ellipt.shorten(text, limit, where=where, unit=unit, marker=marker) == (
                        r.text
                    )


def _prefixes(text: str) -> list[list[str]]:
    clusters = list(ellipt.iter_graphemes(text))
    return [clusters[:k] for k in range(len(clusters) + 1)]
