# ellipt 1.0.0 certification report

The 1.0.0 certification bar (19 items) applied to ellipt. PyPI has no `ellipt` project
(`https://pypi.org/pypi/ellipt/json` answered 404 on 2026-10-18), so 1.0.0 is the first
release there and there is no published version to upgrade from. Every change against
0.2.1, the `main` branch at e2a3fd0 (never published), is still listed in the CHANGELOG.

Progress:
- [x] Branch `release/1.0.0` created from `main` (e2a3fd0, 0.2.1)
- [x] Baseline gates on 0.2.1
- [ ] API review and 1.0.0 changes (item 1)
- [ ] Errors, typing, docstrings and doctests (items 2 to 5)
- [ ] Ground truth: Unicode files fetched live, official test files, reference implementations (item 7)
- [ ] Contract, fuzz and author mutation round (items 6, 9, 18)
- [ ] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [ ] Packaging, e2e and every Python (items 8, 10, 13, 14)
- [ ] Gates (item 15)
- [ ] PR and trace guard CLEAN
- [ ] Five QA lenses (item 19) and independent reviewer (item 16): run by the maintainer next

## Baseline on 0.2.1 (before any change)

On this PC, CPython 3.13.2, from an export of `main` at e2a3fd0: `ruff format --check .`,
`ruff check .` and `mypy --strict src tests` exit 0. Full suite on another machine from a
fresh clone of `main` with the six Unicode files of the manifest present (CPython 3.14.2):
1,882 passed in 14 s (the 853 official grapheme cases run twice: segmentation and
truncation; the wheel test built and installed the wheel). No test checked timing, error
message length or argument types beyond `text`, `marker` and `limit`.

Defects found in 0.2.1 by reading and then reproducing against the exported tree:

- `shorten_path` built every candidate string before measuring any: memory and time grew
  with the square of the path. 1,000, 2,000 and 4,000 directories took 2.1, 8.2 and 32.4 MB
  at peak (0.03, 0.07 and 0.13 s); a 200,000 character path with 50,000 directories needs
  gigabytes.
- Error messages quoted the whole argument: a 100,000 character `where`, `unit` or `sep`
  gave a message of about 100,000 characters, and so did the command line for a huge
  `LIMIT`, `--unit` or `--ambiguous` value.
- `truncate("x", -10**5000)` and `ambiguous=10**5000` raised the interpreter's
  integer-to-string limit error instead of ellipt's own message.
- `ambiguous=2.0` was accepted and `measure("¡", "columns", ambiguous=2.0)` returned
  the float `2.0`; `words="no"` meant word mode; `unit=None` and `where=None` raised
  `ValueError` instead of `TypeError`.
- `iter_graphemes(None)` raised only when iterated.
- A `str` subclass was measured through its own methods (one overriding `__len__` made
  `measure` return 1 for six characters) and came back as itself in `Truncation.text`.
- `Truncation` and the functions reported the private modules `ellipt._core`, ..., so a
  pickled `Truncation` depended on a private module name.
- A limit too small for the marker raised only when the text did not fit
  (`truncate("hi", 2)` returned `"hi"`, `truncate("hello", 2)` raised), and the command
  exited 0 on empty input with such a limit.
- The command expanded tabs by code points, not columns: after two wide characters a tab
  stop of 8 put the next character at column 10. Usage errors and input errors both exited
  1.
- A UNC path with no directory between share and file (`\\server\share\file.txt`) was
  shortened to `\...\share\file.txt`, which reads as a rooted path on the current drive.
- The README linked GUIDE.md, LICENSE and LICENSE-UNICODE relatively (broken on PyPI);
  `scripts/gen_ucd_tables.py` had 202 lines; `scripts/release.ps1` refused any upload once
  the name existed on PyPI.
