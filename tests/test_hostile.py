"""Huge and adversarial input: no crash, no hang, linear time (hand-written shapes)."""

from __future__ import annotations

import time
from collections.abc import Callable

import pytest

from ellipt import ELLIPSIS, UNITS, iter_graphemes, measure, shorten_path, truncate

UNIT = 4_000


def _seconds(work: Callable[[], object]) -> float:
    best = float("inf")
    for _ in range(2):
        start = time.perf_counter()
        work()
        best = min(best, time.perf_counter() - start)
    return best


def _linear(make: Callable[[int], Callable[[], object]]) -> None:
    """Eight times the input may take about eight times as long (a square law is 64)."""
    small = _seconds(make(UNIT))
    large = _seconds(make(8 * UNIT))
    assert large < 20 * max(small, 0.002) + 0.05, (small, large)


TEXTS: dict[str, Callable[[int], str]] = {
    "ascii": lambda n: "abcdefghij" * (n // 10),
    "wide": lambda n: "你好" * (n // 2),
    "combining": lambda n: "é̂" * (n // 3),
    "zwj family": lambda n: "\U0001f468‍\U0001f469‍\U0001f467" * (n // 5),
    "flags": lambda n: "\U0001f1ea\U0001f1f8" * (n // 2),
    "one hangul cluster": lambda n: "ᄀ" * n,
    "words": lambda n: "ab " * (n // 3),
    "one long word": lambda n: "a" * n,
    "zero width": lambda n: "​" * n,
    "heart then vs16 marker": lambda n: "❤" * n,
}


@pytest.mark.parametrize("shape", sorted(TEXTS))
def test_truncate_time_grows_linearly(shape: str) -> None:
    def make(n: int) -> Callable[[], object]:
        text = TEXTS[shape](n)

        def work() -> None:
            for unit in UNITS:
                truncate(text, 80, where="middle", unit=unit, marker=ELLIPSIS)
                truncate(text, 80, where="start", unit=unit, words=True)
            truncate(text, 80, unit="graphemes", words=True, marker="️...")
            truncate(text, 80, where="middle", unit="columns", words=True, marker="️.")
            measure(text, "columns")
            sum(1 for _ in iter_graphemes(text))

        return work

    _linear(make)


PATHS: dict[str, Callable[[int], str]] = {
    "many directories": lambda n: "/".join(["dir"] * (n // 4)) + "/file.txt",
    "long relative root": lambda n: "a" * (n // 2) + "/b" * (n // 4) + "/f.txt",
    "wide directories": lambda n: "/" + "/".join(["世界"] * (n // 3)) + "/f",
    "unc": lambda n: "\\\\host\\share\\" + "\\".join(["d"] * (n // 2)) + "\\f",
    "long name": lambda n: "/x/y/" + "n" * n + ".tar.gz",
    "no separator": lambda n: "n" * n,
    "trailing separators": lambda n: "/a/b" + "/" * n,
    "separators only": lambda n: "/" * n,
}


@pytest.mark.parametrize("shape", sorted(PATHS))
def test_shorten_path_time_grows_linearly(shape: str) -> None:
    def make(n: int) -> Callable[[], object]:
        path = PATHS[shape](n)

        def work() -> None:
            for unit in UNITS:
                shorten_path(path, 40, unit=unit)
            shorten_path(path, 40, marker=ELLIPSIS, sep="/")

        return work

    _linear(make)


def test_a_path_of_200_000_characters_is_shortened_without_building_every_candidate() -> None:
    path = "/".join(["dir"] * 50_000) + "/file.txt"
    start = time.perf_counter()
    assert shorten_path(path, 30) == "dir/.../dir/dir/dir/file.txt"
    assert time.perf_counter() - start < 30


def test_a_marker_that_widens_its_neighbour_backs_off_a_bounded_number_of_times() -> None:
    # Each heart is one column; VS16 at the start of the marker makes the last one two.
    text = "❤" * 100_000
    result = truncate(text, 50_000, unit="columns", marker="️...")
    assert result.size == 50_000 and result.head == "❤" * 49_996
