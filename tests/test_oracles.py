"""Cross-check against independent implementations run live in this test session.

- wcwidth 0.9.2 (https://pypi.org/project/wcwidth/0.9.2/, Unicode 18.0.0 tables): its
  UAX #29 segmenter must agree everywhere; its per code point widths must agree except
  for the policy differences listed below, each class taken from the fetched UCD files.
- ICU through Node.js ``Intl.Segmenter``: it must agree except where its older Unicode
  version explains the difference (a code point it does not know, or GB9c, which
  Unicode 18.0 changed to break no longer between a linker and a following consonant).

Each oracle skips when it is not installed.
"""

from __future__ import annotations

import json
import random
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import UCD, needs_ucd

from ellipt import iter_graphemes, measure

pytestmark = needs_ucd
POOLS = [(0, 0x3400), (0xA000, 0xFFFF), (0x10000, 0x30000), (0x1F000, 0x1FB00), (0xE0000, 0xE0100)]


def _texts(seed: int, count: int) -> list[str]:
    rng = random.Random(seed)
    found: list[str] = []
    while len(found) < count:
        cps = [rng.randrange(*rng.choice(POOLS)) for _ in range(rng.randrange(1, 7))]
        if not any(0xD800 <= cp < 0xE000 for cp in cps):
            found.append("".join(map(chr, cps)))
    return found


def _official() -> list[str]:
    lines = (UCD / "GraphemeBreakTest.txt").read_text(encoding="utf-8").splitlines()
    bodies = [line.split("#", 1)[0].split()[1:] for line in lines if line.split("#", 1)[0]]
    return ["".join(chr(int(t, 16)) for t in b if t not in "÷×") for b in bodies if b]


def _property(name: str, field: int, value: str) -> set[int]:
    found: set[int] = set()
    for raw in (UCD / name).read_text(encoding="utf-8").splitlines():
        parts = [p.strip() for p in raw.split("#", 1)[0].split(";")]
        if len(parts) > field and parts[field] == value:
            first, _, last = parts[0].partition("..")
            found.update(range(int(first, 16), int(last or first, 16) + 1))
    return found


def test_wcwidth_segments_every_text_the_same_way() -> None:
    wcwidth = pytest.importorskip("wcwidth")
    assert wcwidth.list_versions()[-1] == "18.0.0"
    texts = _official() + _texts(1, 60_000)
    wrong = [t for t in texts if list(iter_graphemes(t)) != list(wcwidth.iter_graphemes(t))]
    assert wrong == []


def test_wcwidth_widths_differ_only_by_documented_policy() -> None:
    wcwidth = pytest.importorskip("wcwidth")
    controls = _property("DerivedGeneralCategory.txt", 1, "Cc")
    spacing = _property("DerivedGeneralCategory.txt", 1, "Mc")
    prepended = _property("GraphemeBreakProperty.txt", 1, "Prepend") & _property(
        "DerivedGeneralCategory.txt", 1, "Cf"
    )
    flags = _property("GraphemeBreakProperty.txt", 1, "Regional_Indicator")
    separators = _property("DerivedGeneralCategory.txt", 1, "Zl") | _property(
        "DerivedGeneralCategory.txt", 1, "Zp"
    )
    ignorable = _property("DerivedCoreProperties.txt", 1, "Default_Ignorable_Code_Point")
    letters = _property("DerivedGeneralCategory.txt", 1, "Lo")
    unassigned = _property("DerivedGeneralCategory.txt", 1, "Cn")
    unexplained: list[tuple[str, int, int]] = []
    for cp in range(0x110000):
        if 0xD800 <= cp < 0xE000:
            continue
        mine, theirs = measure(chr(cp), "columns"), wcwidth.wcwidth(chr(cp))
        if mine == theirs:
            continue
        if cp in controls and (mine, theirs) == (0, -1):
            continue  # wcwidth reports controls as -1 (unprintable); ellipt counts 0
        if cp in spacing and theirs == 0 and mine in (1, 2):
            continue  # wcwidth draws spacing marks over the base; ellipt follows wcwidth.c
        if cp in prepended and (mine, theirs) == (0, 1):
            continue  # format characters are zero in ellipt, like U+0600 ARABIC NUMBER SIGN
        if cp in flags and (mine, theirs) == (1, 2):
            continue  # a lone regional indicator is one column in ellipt, a pair is two
        if cp in separators and (mine, theirs) == (1, 0):
            continue  # U+2028 and U+2029 are not controls or format characters in wcwidth.c
        if cp in ignorable and (cp in letters or cp in unassigned) and theirs == 0:
            continue  # Hangul fillers and unassigned ignorables keep their width in ellipt
        unexplained.append((f"U+{cp:04X}", mine, theirs))
    assert unexplained == []


SEGMENT = """
const fs = require('fs');
const texts = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const seg = new Intl.Segmenter('en', {granularity: 'grapheme'});
const out = texts.map(t => [Array.from(seg.segment(t), s => s.index), /\\p{Cn}/u.test(t)]);
fs.writeFileSync(process.argv[3], JSON.stringify({unicode: process.versions.unicode, out}));
"""


def _ends(text: str) -> list[int]:
    starts, position = [], 0
    for cluster in iter_graphemes(text):
        starts.append(position)
        position += len(cluster)
    return starts


def test_icu_segments_the_same_way_up_to_its_unicode_version(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed")
    texts = _official() + _texts(2, 60_000)
    # Node reports UTF-16 indices; compare boundaries as indices into the code points.
    (tmp_path / "seg.js").write_text(SEGMENT, encoding="utf-8")
    (tmp_path / "in.json").write_text(json.dumps(texts), encoding="utf-8")
    command = [node, str(tmp_path / "seg.js"), str(tmp_path / "in.json"), str(tmp_path / "o")]
    subprocess.run(command, check=True, timeout=250)
    result = json.loads((tmp_path / "o").read_text(encoding="utf-8"))
    assert re.fullmatch(r"\d+\.\d+", result["unicode"])
    consonants = _property("DerivedCoreProperties.txt", 2, "Consonant")
    agree = unknown = gb9c = 0
    for text, (units, has_unassigned) in zip(texts, result["out"], strict=True):
        to_cp = {len(text[:i].encode("utf-16-le")) // 2: i for i in range(len(text) + 1)}
        theirs = [to_cp[u] for u in units]
        mine = _ends(text)
        if theirs == mine:
            agree += 1
        elif has_unassigned:
            unknown += 1
        else:
            extra = set(theirs) - set(mine)
            assert not set(mine) - set(theirs), text.encode("unicode_escape")
            assert all(ord(text[i]) in consonants for i in extra), text.encode("unicode_escape")
            gb9c += 1
    assert agree > 0.99 * len(texts) and gb9c < 0.001 * len(texts), (agree, unknown, gb9c)
