"""Every sequence of the official UTS #51 emoji-test.txt, as fetched into data/ucd/.

https://www.unicode.org/Public/18.0.0/emoji/emoji-test.txt (pinned in MANIFEST.json,
fetched 2026-10-19). Each line is one emoji, so it must be one grapheme cluster and
must never be cut apart. A fully-qualified or component emoji is shown in emoji
presentation, which ellipt draws as two columns (GUIDE, "Units"); an unqualified single
code point keeps its text presentation and its East Asian Width.
"""

from __future__ import annotations

import pytest
from conftest import UCD, needs_ucd, ucd_fetched

from ellipt import ELLIPSIS, UNITS, Unit, iter_graphemes, measure, truncate

FIXTURE = UCD / "emoji-test.txt"
pytestmark = needs_ucd


def _lines() -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for raw in FIXTURE.read_text(encoding="utf-8").splitlines():
        body = raw.split("#", 1)[0].strip()
        if body:
            points, status = (part.strip() for part in body.split(";"))
            found.append(("".join(chr(int(h, 16)) for h in points.split()), status))
    return found


LINES = _lines() if ucd_fetched() else []


def test_the_fixture_is_complete() -> None:
    # The status counts are printed at the end of the file itself.
    text = FIXTURE.read_text(encoding="utf-8")
    for status in ("fully-qualified", "minimally-qualified", "unqualified", "component"):
        count = sum(1 for _, s in LINES if s == status)
        assert f"# {status} : {count}\n" in text, status
    assert len(LINES) == 3963 + 1029 + 243 + 9


def test_every_emoji_is_one_grapheme_cluster() -> None:
    wrong = [e for e, _ in LINES if list(iter_graphemes(e)) != [e]]
    assert wrong == []


def test_emoji_presentation_is_two_columns() -> None:
    shown = [e for e, s in LINES if s in ("fully-qualified", "component")]
    assert len(shown) == 3972
    assert [e for e in shown if measure(e, "columns") != 2] == []


def _east_asian_width(cp: int) -> str:
    for raw in (UCD / "EastAsianWidth.txt").read_text(encoding="utf-8").splitlines():
        body = raw.split("#", 1)[0].strip()
        if body:
            points, value = (part.strip() for part in body.split(";"))
            first, _, last = points.partition("..")
            if int(first, 16) <= cp <= int(last or first, 16):
                return value
    return "N"


def test_unqualified_single_code_points_keep_text_presentation() -> None:
    single = [e for e, s in LINES if s == "unqualified" and len(e) == 1]
    assert len(single) > 200
    wide = {e for e in single if _east_asian_width(ord(e)) in ("W", "F")}
    assert len(wide) == 6  # CJK symbols such as U+3030 WAVY DASH are wide as text too
    assert [e for e in single if measure(e, "columns") != (2 if e in wide else 1)] == []


@pytest.mark.parametrize("unit", UNITS)
def test_no_emoji_is_ever_cut_apart(unit: Unit) -> None:
    for emoji, _ in LINES[::7]:
        text = "ab" + emoji + "cd"
        n = len(emoji)
        bounds = {0, 1, 2, 2 + n, 3 + n, 4 + n}
        for limit in range(measure(ELLIPSIS, unit), measure(text, unit) + 1):
            for where in ("end", "start", "middle"):
                r = truncate(text, limit, where=where, unit=unit, marker=ELLIPSIS)
                assert len(r.head) in bounds and len(text) - len(r.tail) in bounds, r
