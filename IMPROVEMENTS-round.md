# Improvements for this round

Progress:

- [x] Brainstorm (this file)
- [x] UCD snapshot, generator and embedded tables (Unicode 18.0.0)
- [x] Grapheme-safe cutting and the four units (chars, graphemes, columns, bytes)
- [x] Typed `Truncation` result, word-aware cutting, `measure`
- [x] Path-aware middle truncation (`shorten_path`)
- [x] Command line tool
- [x] Docs: docstrings, README, GUIDE, CHANGELOG, version bump
- [ ] Contract test, GraphemeBreakTest conformance, seeded fuzz, wheel e2e
- [ ] Gates green, pull request opened
- [ ] Independent review findings fixed, trace guard clean

Ranked by user impact. Every item is additive: `shorten(text, width, *, where, marker,
width_aware)` keeps its name, parameters and return type. New behaviour arrives through
new functions and keyword-only parameters.

1. **Never cut inside a grapheme cluster.** 0.1.0 walks code points, so it can split
   `e` from its combining accent, half a flag (two regional indicators) or a ZWJ emoji
   family, leaving a broken glyph next to the marker. Segment with UAX #29 extended
   grapheme clusters from tables generated out of a committed UCD 18.0.0 snapshot (the
   same data version and generator approach as the sibling `bytetrunc` and `cellstr`
   libraries, with no runtime dependency on them). The official GraphemeBreakTest.txt
   runs in the suite.
2. **Choose the unit of the limit.** `unit="chars"` (code points, the 0.1.0 default),
   `"graphemes"` (user-perceived characters), `"columns"` (terminal display cells per
   UAX #11 with emoji sequences as one wide glyph) and `"bytes"` (UTF-8, for database
   columns and protocol fields). `width_aware=True` stays as the spelling of
   `unit="columns"`. The marker is measured in the same unit and counted inside the
   limit, so the result never exceeds it in any unit.
3. **Typed result.** `truncate(...)` returns a frozen `Truncation` with `text`, `head`,
   `marker`, `tail`, `original`, `unit`, `limit` and `size`, plus `truncated`,
   `removed` and `removed_span`, so callers can show a tooltip with the full text, log
   what was dropped, or highlight the cut without re-deriving it.
4. **Path-aware middle truncation.** `shorten_path` keeps the root and the file name
   and drops whole directories from the middle, the way macOS Finder and editor tab
   titles do (`/home/me/.../src/main.py`). When even the name does not fit it cuts the
   middle of the stem and keeps the extension.
5. **Word-aware cutting.** `words=True` backs the cut off to whitespace so the end of
   a sentence does not stop mid word (CSS `text-overflow: ellipsis` cuts mid word; a
   title or preview usually should not). Falls back to a hard cut when one word fills
   the whole budget.
6. **Better middle balance.** Leftover budget from the left half (a wide character
   that did not fit) is handed to the right half instead of being wasted.
7. **`ELLIPSIS` constant and guidance.** U+2026 HORIZONTAL ELLIPSIS is one column and
   one code point but three UTF-8 bytes; `"..."` is three of everything. Export the
   constant and document when to pick which.
8. **`measure(text, unit)`** exposes the same measurement the truncation uses.
9. **Command line tool.** `ellipt LIMIT` truncates every line of stdin or files, with
   `--where`, `--unit`, `--marker`, `--words`, `--path` and `--ambiguous`; errors go to
   stderr with exit status 1.
10. **Docs.** Docstrings with doctests, a README with runnable examples, a GUIDE with the
    rules, sources and edge cases, and a CHANGELOG entry. Minor version bump to 0.2.0.
11. **Proof.** Contract test over the whole promise, the official grapheme test file,
    seeded fuzz (within the limit, prefix and suffix of the input, never splits a
    cluster), and an end to end test that builds the wheel, installs it into a fresh
    venv and drives the installed script.

Out of scope: ANSI escape sequences (strip them first or use a terminal-aware library),
locale-specific word segmentation (UAX #29 word boundaries for scripts without spaces).
