# ellipt 1.0.0 certification report

The 1.0.0 certification bar (19 items) applied to ellipt. PyPI has no `ellipt` project
(`https://pypi.org/pypi/ellipt/json` answered 404 on 2026-10-18 and again on 2026-10-19),
so 1.0.0 is the first release there and there is no published version to upgrade from.
Every change against 0.2.1, the `main` branch at e2a3fd0 (never published), is still
listed in the CHANGELOG.

Progress:
- [x] Branch `release/1.0.0` created from `main` (e2a3fd0, 0.2.1)
- [x] Baseline gates on 0.2.1
- [x] API review and 1.0.0 changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Ground truth: Unicode files fetched live, official test files, reference implementations (item 7)
- [x] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [x] Packaging, e2e and every Python (items 8, 10, 13, 14)
- [x] Gates (item 15)
- [x] PR and trace guard CLEAN
- [ ] Five QA lenses (item 19) and independent reviewer (item 16): run by the maintainer next

## Scorecard (author)

| # | Item | Result |
| --- | --- | --- |
| 1 | Public API reviewed for stability | PASS: 11 names; signatures, parameter names, defaults and `Truncation` fields pinned by `tests/test_contract_api.py`; one rename (`iter_graphemes(s)` to `text`) and every behaviour change in the CHANGELOG |
| 2 | `__all__` exact, no private imports in docs | PASS |
| 3 | Docstrings with runnable examples, doctests | PASS: every public name and `Truncation` member has a doctest; README and GUIDE outputs run as tests |
| 4 | Typed end to end | PASS: `mypy --strict src tests`, `py.typed` shipped, no `Any` in the public API |
| 5 | Typed, documented, bounded errors | PASS: `TypeError` / `ValueError` per argument (GUIDE "Errors"), values quoted up to 40 characters, huge integers by size |
| 6 | Contract tests of every public name | PASS |
| 7 | Real ground truth | PASS: see below |
| 8 | Real e2e from the wheel | PASS: built sdist and wheel, contents pinned, wheel installed in a fresh venv and driven from an empty folder with `-I`, CLI by subprocess; no PyPI release to upgrade from |
| 9 | Seeded fuzz, no crash, hang or blowup | PASS |
| 10 | Supported Pythons | PASS: CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2, 3.14.2t; 3.9 refused by `requires-python` |
| 11 | README and `twine check` | PASS: `twine check --strict`, absolute links, certified badge |
| 12 | Dated CHANGELOG section | PASS: 1.0.0, 2026-10-19 |
| 13 | pyproject 1.0.0, Production/Stable | PASS |
| 14 | sdist and wheel contents | PASS |
| 15 | Gates each exit 0 | PASS: see Gates |
| 16 | Independent reviewer | pending (maintainer) |
| 17 | PR and trace guard | PR from `release/1.0.0`, trace guard CLEAN; merge and publish left to the maintainer |
| 18 | Contracts bite (mutations) | PASS: author 30, all killed (5 survivors in the first pass, contracts added) |
| 19 | Five independent QA lenses | pending (maintainer) |

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

## API review (item 1)

Kept from 0.2.1: `truncate`, `shorten`, `shorten_path`, `measure`, `iter_graphemes`,
`Truncation`, `ELLIPSIS`, `UNITS`, `UNICODE_VERSION`, `Unit` and `Where`, with their
positional and keyword-only parameters and defaults; `shorten` keeps the 0.1.0
signature; the command line keeps its options. Changed (CHANGELOG 1.0.0): every argument
checked before the text, a marker larger than the limit refused even when the text fits,
stricter types (`bool` flags, integer `ambiguous`, `__index__` integers accepted),
`iter_graphemes(text)` raising at the call, `str` subclasses read as plain strings,
bounded messages, public objects (and the `Truncation` property getters) reporting
`ellipt` as their module, linear `shorten_path`, exit status 2 for usage errors.

## Ground truth (item 7)

`data/ucd/MANIFEST.json` pins seven Unicode 18.0.0 files (URL, size, sha256, licence);
`scripts/fetch_upstream.py` re-fetched all seven live on 2026-10-19 and every checksum
matched. Nothing fetched is committed or shipped; the tests skip without the files.

- UCD files (DerivedCoreProperties, DerivedGeneralCategory, EastAsianWidth,
  GraphemeBreakProperty, emoji-data): the generator runs in the suite and its output
  must equal the embedded tables byte for byte.
- `GraphemeBreakTest.txt` (https://www.unicode.org/Public/18.0.0/ucd/auxiliary/): all 853
  official cases through the segmenter and through every truncation of each case.
- `emoji-test.txt` (https://www.unicode.org/Public/18.0.0/emoji/emoji-test.txt, added and
  fetched 2026-10-19): all 5,244 sequences are one grapheme cluster; the 3,972
  fully-qualified and component ones are two columns; the unqualified single code points
  keep their East Asian Width; no truncation in any unit cuts one apart.
- wcwidth 0.9.2 (Unicode 18.0.0), run live: its segmenter agrees on the 853 official
  cases and on 60,000 seeded strings over all planes (200,000 more in exploration, no
  difference). Widths compared over the whole code space: every difference falls in a
  policy class taken from the fetched files (controls, spacing marks, prepended
  concatenation marks, lone regional indicators, U+2028 and U+2029, ignorable Hangul
  fillers and unassigned ignorables), each listed in the GUIDE.
- ICU 78.3 (Unicode 17.0) through Node.js 24.18.0 `Intl.Segmenter`, run live: on 191,079
  strings in exploration, 71 differences, 60 with a code point unassigned in Unicode 17
  and 11 from the GB9c change of Unicode 18 (a consonant before the linker is no longer
  required, as the fetched UAX #29 text states). The suite asserts on 60,853 strings that
  every difference is one of these two kinds.
- Hand-written expectations (path shapes, CLI lines, edge contracts) are written as such
  in their test files, never presented as fetched.

## Fuzz and hostile input (item 9)

`tests/test_fuzz.py`: 40 seeds of 150 random texts over hostile pieces (controls, a lone
surrogate, ZWJ, VS15 and VS16, regional indicators, Hangul jamo, Indic conjuncts,
prepend) through every unit, position, marker and `words`, checking the whole promise;
20 seeds for `shorten_path`. `tests/test_hostile.py`: 10 text shapes and 8 path shapes
timed at 4,000 and 32,000 characters (growth must stay linear), a 200,000 character path
with 50,000 directories, a VS16 marker that widens its neighbour on 100,000 hearts.
`tests/test_errors.py` and `tests/test_cli_errors.py`: 100,000 character values in every
argument and option give messages of at most 160 and 300 characters.

## Author mutation round (item 18)

30 mutants over every module, each applied alone to a fresh clone of the pushed branch
on another machine, the full suite (fetched files, wcwidth and Node.js present) run with
`-x`, a 300 s per-test limit and no bytecode cache; the unmutated suite passed before
and after (1,990 passed). Pass 1 at e485bda plus the test fixes: 25 killed, 5 survived
(9, 23, 25, 27, 30). Contracts added in `tests/test_contract_edges.py` (6eed17b). Pass 2
at 6eed17b: all 30 killed.

| # | Mutation | Module | Killed by |
| --- | --- | --- | --- |
| 1 | off-by-one in the greedy head | `_cut.py` | `tests/test_cli.py::test_lines_are_truncated` |
| 2 | middle gives the left side the smaller half | `_cut.py` | `tests/test_contract_edges.py::test_middle_hands_budget_the_tail_cannot_use_back_to_the_head` |
| 3 | word snap may return an empty head | `_cut.py` | `tests/test_docs_examples.py::test_documented_results_are_true` |
| 4 | first budget one too large | `_core.py` | `tests/test_docs_examples.py::test_documented_results_are_true` |
| 5 | end window one code point short | `_core.py` | `tests/test_contract.py::test_the_whole_promise_holds_for_every_unit_position_and_limit` |
| 6 | marker equal to the limit refused | `_core.py` | `tests/test_cli.py::test_lines_are_truncated` |
| 7 | result not re-measured after joining the marker | `_core.py` | `tests/test_fuzz.py::test_truncate_keeps_its_promise` |
| 8 | bytes counted as code points | `_measure.py` | `tests/test_cli.py::test_lines_are_truncated` |
| 9 | emoji with VS15 counted wide (survived pass 1) | `_width.py` | `tests/test_contract_edges.py::test_an_emoji_with_vs15_is_one_column_and_with_vs16_two` |
| 10 | flag counted as one column | `_width.py` | `tests/test_doctests.py::test_docstring_examples_pass` |
| 11 | ambiguous width ignored | `_width.py` | `tests/test_cli.py::test_lines_are_truncated` |
| 12 | GB9c without the linker | `_graphemes.py` | `tests/test_grapheme_conformance.py::test_official_case` |
| 13 | regional indicator pairing swapped | `_graphemes.py` | `tests/test_doctests.py::test_docstring_examples_pass` |
| 14 | GB11 without the ZWJ state | `_graphemes.py` | `tests/test_grapheme_conformance.py::test_official_case` |
| 15 | bool accepted as an int | `_checks.py` | `tests/test_errors.py::test_wrong_types_raise_type_error_at_the_call` |
| 16 | long values quoted ten times longer | `_checks.py` | `tests/test_errors.py::test_bad_values_raise_short_value_errors` |
| 17 | str subclass kept as given | `_checks.py` | `tests/test_errors.py::test_a_str_subclass_is_measured_and_returned_as_a_plain_str` |
| 18 | wrong error type for a bad flag | `_checks.py` | `tests/test_errors.py::test_wrong_types_raise_type_error_at_the_call` |
| 19 | compound .tar extension dropped | `_path.py` | `tests/test_path.py::test_compound_extensions_stay_together` |
| 20 | UNC root kept without a share | `_pathcut.py` | `tests/test_fuzz.py::test_shorten_path_stays_within_the_limit` |
| 21 | candidate skipped at an exact fit | `_pathcut.py` | `tests/test_contract_edges.py::test_trailing_separators_stay_with_the_last_directory` |
| 22 | empty path marker accepted | `_path.py` | `tests/test_cli.py::test_usage_errors_exit_2_before_reading_input` |
| 23 | separator arguments swapped (survived pass 1) | `_path.py` | `tests/test_contract_edges.py::test_trailing_separators_stay_with_the_last_directory` |
| 24 | tab stop ignores the column | `_cli_io.py` | `tests/test_cli.py::test_ellipsis_flag_tabs_and_bom` |
| 25 | CRLF split into CR and LF (survived pass 1) | `_cli_io.py` | `tests/test_contract_edges.py::test_line_endings_are_kept_and_only_the_first_bom_is_dropped` |
| 26 | usage errors exit 1 | `_cli.py` | `tests/test_cli.py::test_usage_errors_exit_2_before_reading_input` |
| 27 | BOM dropped on every line (survived pass 1) | `_cli_io.py` | `tests/test_contract_edges.py::test_line_endings_are_kept_and_only_the_first_bom_is_dropped` |
| 28 | width_aware conflict not checked | `_shorten.py` | `tests/test_errors.py::test_bad_values_raise_short_value_errors` |
| 29 | public names left in private modules | `__init__.py` | `tests/test_contract_api.py::test_public_objects_report_the_package_as_their_module` |
| 30 | middle hands no leftover back to the head (survived pass 1) | `_cut.py` | `tests/test_contract_edges.py::test_middle_hands_budget_the_tail_cannot_use_back_to_the_head` |

## Packaging, e2e and Pythons (items 8, 10, 13, 14)

- `tests/test_e2e_wheel.py` builds the sdist and wheel with `python -m build`, pins the
  wheel's file list (the package modules, `py.typed`, both licences, no data, tests or
  scripts) and its metadata (version, Production/Stable, no runtime requirement), checks
  the sdist (sources, tests, docs, both licences, the manifest, no fetched `.txt` files,
  no caches or reports), installs the wheel in a fresh venv, runs a consumer script from
  an empty folder with `-I`, and drives the installed `ellipt` script and `python -m
  ellipt` by subprocess (exit statuses 0, 1 and 2, BOM, tabs, files, `--version`,
  `--help`).
- `twine check --strict` passes for both files built at 6eed17b.
- Every interpreter on this PC from `requires-python` up, at 6eed17b, the wheel installed
  in a fresh venv and the sdist's own suite run against the installed package (fetched
  files, wcwidth and Node.js present; `src` taken off the path): CPython 3.10.19, 3.11.5,
  3.12.12, 3.13.2, 3.14.2 and 3.14.2 free-threaded, 1,987 passed each (the three e2e
  tests need the source tree and ran in the full suite). CPython 3.9.25 refuses the wheel
  (`requires-python >=3.10`); 3.8 is below it too.

## Gates (item 15)

At 6eed17b on another machine from a fresh clone of `release/1.0.0` (CPython 3.14), with
the seven fetched Unicode files, wcwidth 0.9.2 and Node.js present, each command on its
own: `scripts/gen_ucd_tables.py --check`, `ruff format --check .`, `ruff check .`,
`mypy --strict src`, `mypy --strict src tests` and `pytest` (1,990 passed, no skips, in
217 s) all exit 0. On this PC (CPython 3.13.2) the four static gates exit 0 as well.
