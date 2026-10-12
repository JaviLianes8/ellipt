"""Seeded fuzz over the whole promise: within the limit, prefix and suffix, whole clusters."""

from __future__ import annotations

import random

import pytest

from ellipt import UNITS, iter_graphemes, measure, shorten_path, truncate

PIECES = [
    "a", "Z", " ", "  ", "\t", "\r\n", "\n", "\x00", "\x1b", "-", "/", "\\", ".",
    "e\u0301", "\u0301", "\u200d", "\ufe0f", "\ufe0e", "\u2764", "\u00ad", "\u00a1",
    "\U0001f1ea", "\U0001f1f8", "\U0001f468", "\U0001f3fd", "\U0001f9d1\u200d\U0001f4bb",
    "\u4e16", "\uff21", "\u1100", "\u1161", "\u11a8", "\uac00", "\u0915\u094d\u0937",
    "\u0600", "\U000e0067", "\u2026", "\U0001f600", "\u0e33", "\ud800",
]  # fmt: skip
MARKERS = ["...", "\u2026", "", "~", "\u4e00", "[\u2026]", "\u0301"]


def _text(rng: random.Random) -> str:
    return "".join(rng.choice(PIECES) for _ in range(rng.randrange(0, 14)))


def _bounds(text: str) -> set[int]:
    ends = {0}
    position = 0
    for cluster in iter_graphemes(text):
        position += len(cluster)
        ends.add(position)
    return ends


@pytest.mark.parametrize("seed", range(40))
def test_truncate_keeps_its_promise(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(150):
        text = _text(rng)
        unit = rng.choice(UNITS)
        where = rng.choice(("start", "middle", "end"))
        marker = rng.choice(MARKERS)
        ambiguous = rng.choice((1, 2))
        limit = rng.randrange(0, 24)
        words = rng.random() < 0.3
        args = {"where": where, "unit": unit, "marker": marker, "ambiguous": ambiguous}
        if measure(text, unit, ambiguous=ambiguous) > limit and (
            measure(marker, unit, ambiguous=ambiguous) > limit
        ):
            with pytest.raises(ValueError, match="does not fit"):
                truncate(text, limit, words=words, **args)  # type: ignore[arg-type]
            continue
        r = truncate(text, limit, words=words, **args)  # type: ignore[arg-type]
        context = f"{text!r} {limit} {args} words={words}"
        assert r.size == measure(r.text, unit, ambiguous=ambiguous) <= limit, context
        assert r.text == r.head + r.marker + r.tail, context
        assert text.startswith(r.head) and text.endswith(r.tail), context
        bounds = _bounds(text)
        assert len(r.head) in bounds and len(text) - len(r.tail) in bounds, context
        fits = measure(text, unit, ambiguous=ambiguous) <= limit
        assert r.truncated is not fits, context
        assert r.head + r.removed + r.tail == text, context
        if where == "end" or fits:
            assert r.tail == "", context
        if where == "start" and not fits:
            assert r.head == "", context


@pytest.mark.parametrize("seed", range(20))
def test_shorten_path_stays_within_the_limit(seed: int) -> None:
    rng = random.Random(1000 + seed)
    for _ in range(100):
        parts = [_text(rng).replace("/", "").replace("\\", "") for _ in range(rng.randrange(1, 6))]
        path = rng.choice(("/", "", "C:\\", "~/")) + rng.choice(("/", "\\")).join(parts)
        unit = rng.choice(UNITS)
        marker = rng.choice(("...", "\u2026"))
        limit = rng.randrange(measure(marker, unit), 30)
        result = shorten_path(path, limit, unit=unit, marker=marker)
        assert measure(result, unit) <= limit, (path, limit, unit)
        if measure(path, unit) <= limit:
            assert result == path
