# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
