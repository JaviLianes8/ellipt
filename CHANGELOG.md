# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-19

First stable release, and the first one published on PyPI (0.1.0 to 0.2.1 were never
uploaded there). The public API is now stable under Semantic Versioning: the names in
`ellipt.__all__`, their signatures, parameter names and defaults, the fields of
`Truncation`, the exceptions they raise, the units and the command line options.
Changes against 0.2.1:

### Changed

- Every argument is checked before the text is examined. A marker larger than the limit
  now raises `ValueError` even when the text fits (`truncate("hi", 2)` used to return
  `"hi"`), and the command reports it before reading any input.
- Stricter types: `ambiguous` must be an integer (a float such as `2.0` raises
  `TypeError` instead of turning sizes into floats), `words` and `width_aware` must be
  `bool` (`words="no"` used to mean word mode), and `unit=None` or `where=None` raise
  `TypeError` instead of `ValueError`. Integer types other than `int` with `__index__`
  are accepted for limits and `ambiguous`.
- `iter_graphemes` names its parameter `text` (it was `s`) and raises `TypeError` for a
  non-`str` argument at the call, not on the first `next()`.
- A `str` subclass is measured as the plain string it holds and every string in the
  result is a plain `str`.
- Error messages are bounded: strings are quoted up to 40 characters and huge integers
  are described by their size, instead of being repeated whole (a 100,000 character
  `where` gave a 100,000 character message, and `-(10**5000)` failed inside `str()`).
- `Truncation` and the public functions report `ellipt` as their module, so a pickled
  `Truncation` no longer names a private module.
- `shorten_path` runs in linear time and memory; it used to build every candidate
  string, which needed gigabytes for a path with 50,000 directories. A UNC path with no
  directory between share and file is no longer shortened to `\...\share\file`,
  which read as a rooted path on the current drive.
- Command line: usage errors exit with status 2 (input errors keep 1), messages are
  bounded, `--tabsize` expands tabs by display columns (wide characters count as two),
  and a closed standard input or output is reported instead of raising.

### Added

- Tests against the official Unicode `emoji-test.txt` (5,244 sequences) and against two
  independent segmenters (`wcwidth` 0.9.2 and the ICU segmenter in Node.js), contract
  tests that pin the public surface and every error path, and timing tests for hostile
  input.

## [0.2.1]

### Changed

- The Unicode Character Database files are no longer committed. `data/ucd/MANIFEST.json`
  pins them to Unicode 18.0.0 (URL, size, sha256, licence) and `scripts/fetch_upstream.py`
  fetches them; the generator check and the conformance tests skip until then. The
  generated tables stay in the package and the Unicode licence notice ships in the wheel.
- The sdist ships only the sources, tests, scripts and docs.

## [0.2.0]

### Added

- `truncate` returns a frozen `Truncation` with `text`, `head`, `marker`, `tail`,
  `original`, `unit`, `limit` and `size`, plus `truncated`, `removed` and
  `removed_span`.
- `unit=` on `shorten` and `truncate`: `"chars"`, `"graphemes"`, `"columns"` or
  `"bytes"` (UTF-8). `measure(text, unit)` exposes the same measurement.
- `words=True` cuts at whitespace when it can.
- `shorten_path` drops whole directories from the middle and keeps the root and the
  file name, then shortens the stem and keeps the extension.
- `ambiguous=` (1 or 2) sets the width of East Asian Ambiguous characters.
- `ELLIPSIS` (U+2026), `UNITS`, `UNICODE_VERSION` and `iter_graphemes`.
- The `ellipt` command truncates every line of standard input or files.
- Unicode 18.0.0 tables generated from a committed UCD snapshot, with the official
  GraphemeBreakTest.txt in the test suite.

### Changed

- The cut never splits an extended grapheme cluster (UAX #29): accents, flags, emoji
  ZWJ sequences and CR LF stay whole.
- `width_aware=True` now measures grapheme clusters, so emoji sequences count as one
  two-column glyph and the width data follows Unicode 18.0.0.
- In the middle position, budget the left side cannot use goes to the right side.
- Wrong argument types now raise `TypeError`: a non-str `text` or `marker`, and a
  `width` that is not an int (a float or a bool).
- Error messages say "limit" instead of "width" and name the unit.
- With `width_aware=True`, control characters such as tab count as zero columns
  (0.1.0 counted them as one), following wcwidth. Expand tabs first if they matter.

## [0.1.0]

- First release: `shorten` truncates a string with an ellipsis at the start,
  middle or end, by character count or display width, with a configurable marker.
