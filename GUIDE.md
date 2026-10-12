# ellipt guide

This guide states the exact rules `ellipt` follows, where its Unicode data comes from,
and how it behaves at the edges.

## The promise

For `truncate(text, limit, where=..., unit=..., marker=..., words=..., ambiguous=...)`:

1. If `text` already fits in `limit`, it comes back whole and `truncated` is false.
2. Otherwise the result is `head + marker + tail`, where `head` is a prefix and `tail`
   a suffix of `text`. With `where="end"` the tail is empty, with `where="start"` the
   head is empty, and with `where="middle"` both ends are kept.
3. `head` and `tail` end on extended grapheme cluster boundaries of `text` (UAX #29).
4. The size of the result, measured in `unit`, never exceeds `limit`. The marker is
   measured in the same unit and counted inside the limit.
5. A marker larger than the limit raises `ValueError`, as do a negative limit and an
   unknown `where`, `unit` or `ambiguous`. Wrong types raise `TypeError`.

`shorten` returns `truncate(...).text`. `shorten_path` keeps promises 1, 3 (at
separators and in the file name) and 4.

## Units

| unit | counts | use it for |
| --- | --- | --- |
| `chars` | code points, `len(s)` | the 0.1.0 default, Python-side limits |
| `graphemes` | extended grapheme clusters | "characters" as a reader counts them |
| `columns` | terminal display cells | tables, status lines, fixed-width output |
| `bytes` | UTF-8 bytes | database columns, file names, protocol fields |

Columns follow UAX #11 East Asian Width with Markus Kuhn's wcwidth rules: controls,
nonspacing and enclosing marks, format characters (except SOFT HYPHEN) and Hangul medial
vowels and final consonants are zero; Wide and Fullwidth are two; East Asian Ambiguous
characters are `ambiguous` cells (1 by default, 2 for CJK terminals); everything else is
one. A grapheme cluster that draws as one emoji (VS16, a skin tone, a ZWJ sequence, a
tag sequence or a flag) is two cells, and an emoji with VS15 is one. These are the same
rules and the same data as the sibling `cellstr` library.

```python
from ellipt import ELLIPSIS, measure, truncate

measure("\u2500\u2500", "columns")  # -> 2
measure("\u2500\u2500", "columns", ambiguous=2)  # -> 4
measure("\u2764\ufe0f", "columns")  # -> 2
measure("e\u0301", "graphemes")  # -> 1
```

## Choosing a marker

U+2026 HORIZONTAL ELLIPSIS is one code point, one grapheme and one column, so it leaves
two more units of text than `"..."` in those units. In UTF-8 both are three bytes. CSS
`text-overflow: ellipsis` renders U+2026. The default stays `"..."` because it is plain
ASCII and safe in every encoding and font; pass `marker=ELLIPSIS` for typographic output.
Any string works, including `""` for a hard cut and `" [...] "` for prose.

```python
truncate("abcdefgh", 5).text  # -> 'ab...'
truncate("abcdefgh", 5, marker=ELLIPSIS).text  # -> 'abcd\u2026'
```

## Where to cut

- `end` keeps the start, like CSS `text-overflow: ellipsis`. Good for titles and
  previews.
- `start` keeps the end. Good for log lines, long ids and anything whose tail matters.
- `middle` keeps both ends, the way macOS Finder and editors shorten file names. The
  left side gets the larger half; when a wide cluster stops it early, the spare budget
  goes to the right side, then back to the left.

```python
truncate("a\u4f60bcdefgh", 5, where="middle", unit="columns", marker=".").text  # -> 'a.fgh'
```

## Words

`words=True` moves each cut to whitespace (any character for which `str.isspace` is
true) and drops the whitespace next to the marker. In the middle position the budget a
snap frees on one side is offered to the other side, again on word boundaries. It does
not use dictionary-based word segmentation, so text without spaces (Chinese, Japanese,
Thai) gets a hard cut at a grapheme boundary. If a single word fills the whole budget,
the cut is hard too, rather than returning only the marker.

```python
truncate("Supercalifragilistic", 8, words=True).text  # -> 'Super...'
truncate("one two three", 11, where="start", words=True).text  # -> '...three'
truncate("a b c d e f", 7, where="middle", words=True).text  # -> 'a...e f'
```

## Paths

`shorten_path` keeps the first component (`/`, `C:\`, `~/`, `\\server\share\`, or the top
directory of a relative path) and the file name, and keeps as many directories next to the file name as
fit. The order of fallbacks is:

1. `root + marker + /dir/.../name`, dropping directories from the root side first;
2. `marker + /name`;
3. `name` alone, when it fits;
4. the name shortened in the middle of its stem with the extension kept (`.tar.gz`,
   `.tar.xz` and other `.tar.*` extensions stay together);
5. the name shortened in the middle.

Both `/` and `\` count as separators unless `sep` names one. A trailing separator stays
with the last directory. An empty marker is rejected, because `a/b/c` cut to `a//c`
would read as a different, real path.

```python
from ellipt import shorten_path

shorten_path(r"C:\Users\me\AppData\Local\Temp\build.log", 24)  # -> 'C:\\...\\Temp\\build.log'
shorten_path("/srv/www/site/public/", 16)  # -> '/.../public/'
```

## Edge cases

- A marker that would merge with the neighbouring cluster (for example one that starts
  with U+FE0F or a combining mark) can change the measured size. The result is measured
  again after joining and the cut backs off until it fits.
- Lone surrogates are counted as three bytes (the `surrogatepass` encoding) so strings
  from `os.fsdecode` do not crash the byte unit.
- CR LF is a single grapheme cluster and is never split.
- Tabs and other control characters are zero columns, as in wcwidth. The library does
  not know your tab stops, so expand tabs first (`s.expandtabs()`); the command line tool
  does this for you with `--tabsize`.
- ANSI escape sequences are measured as ordinary text. Strip them first.
- Long inputs: an end cut in `chars` or `bytes` only segments the first `limit + 1` code
  points. Other cuts segment the whole string once, which is linear in its length.

## Unicode data

The tables in `src/ellipt/_ucd_*.py` are generated by `scripts/gen_ucd_tables.py` from
the Unicode 18.0.0 files in `data/ucd/`, fetched unmodified from unicode.org (URLs and
SHA-256 checksums in `data/ucd/SOURCES.txt`). The test suite regenerates the tables and
compares them byte for byte, checks the checksums, and runs all 853 cases of the official
`GraphemeBreakTest.txt` through both the segmenter and the truncation engine.

To move to a new Unicode version, replace the files in `data/ucd/`, update
`SOURCES.txt`, run `python scripts/gen_ucd_tables.py` and update the expected case count
in `tests/test_grapheme_conformance.py`.
