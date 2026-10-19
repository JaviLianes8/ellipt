# ellipt

[![Lianes8 Certified](https://lianes8studio.com/certified/lianes8-certified-badge.svg)](https://lianes8studio.com/certified)

Truncate strings with an ellipsis at the start, middle or end, and be sure the result
fits. A limit can count code points, grapheme clusters, terminal columns or UTF-8 bytes;
the marker is counted inside the limit; the cut never splits an accent, a flag or an
emoji sequence; and you get back exactly what was removed. Typed, zero dependencies,
Unicode 18.0.0 tables embedded, with a command line tool for pipes.

## The problem

`s[:n] + "..."` is longer than `n`, splits `"café"` into `"cafe"` and leaves half
of an emoji ZWJ sequence behind. Counting `len(s)` is wrong for a terminal (`"你好"`
is two code points but four columns) and wrong for a database column or a file name
limited in bytes. Keeping the end of a log line or both ends of a path needs more code
again. `ellipt` does all of it with one call and one guarantee: the result never exceeds
the limit in the unit you chose.

## Install

```
pip install ellipt
```

## Usage

```python
from ellipt import ELLIPSIS, measure, shorten, shorten_path, truncate

shorten("hello world", 8)  # -> 'hello...'
shorten("hello world", 8, where="start")  # -> '...world'
shorten("hello world", 9, where="middle")  # -> 'hel...rld'
shorten("hello world", 6, marker=ELLIPSIS)  # -> 'hello…'

# Text that already fits is returned unchanged.
shorten("short", 20)  # -> 'short'
```

### Pick the unit of the limit

```python
family = "\U0001f468\u200d\U0001f469\u200d\U0001f467"  # one emoji, five code points
text = "ab" + family + "cd"

measure(text, "chars")  # -> 9
measure(text, "graphemes")  # -> 5
measure(text, "columns")  # -> 6
measure(text, "bytes")  # -> 22

# The family is kept whole or dropped whole, never cut into pieces.
shorten(text, 6, marker=ELLIPSIS)  # -> 'ab…'
shorten(text, 4, unit="graphemes", marker=ELLIPSIS)  # -> 'ab👨\u200d👩\u200d👧…'
shorten("你好世界", 5, unit="columns", marker=ELLIPSIS)  # -> '你好…'
shorten("café crème", 8, unit="bytes", marker="")  # -> 'café cr'
```

`width_aware=True` from 0.1.0 still works and means `unit="columns"`.

### Know what was removed

```python
r = truncate("The quick brown fox jumps", 14, words=True, marker=ELLIPSIS)
r.text  # -> 'The quick…'
r.removed  # -> ' brown fox jumps'
r.truncated  # -> True
r.size <= r.limit  # -> True
```

`words=True` backs the cut off to whitespace; with one long word it cuts hard instead.

### Shorten paths the way file browsers do

```python
shorten_path("/home/me/projects/app/src/main.py", 20)  # -> '/.../app/src/main.py'
shorten_path("/home/me/projects/app/src/main.py", 11)  # -> '.../main.py'
shorten_path("photos/an_extremely_long_holiday_name.jpeg", 20)  # -> 'an_ext...y_name.jpeg'
```

## Command line

```
$ printf 'hello world
' | ellipt 8
hello...
$ git ls-files | ellipt 28 --path
$ ellipt 30 --where middle --ellipsis notes.txt
$ ellipt 255 --unit bytes --marker "" < titles.txt
```

The command reads standard input (or the files given) as UTF-8, keeps each LF or CRLF
line ending, and counts terminal columns by default, expanding tabs to 8-column stops
first (`--tabsize`). `--ellipsis` uses U+2026 as the marker without having to type it.
`ellipt --help` lists every option. The exit status is 0 on success (also when the
reader stops early, as with `| head`), 1 when an input cannot be read or is not UTF-8,
and 2 for a usage error such as a marker that does not fit in the limit; errors go to
standard error.

## Why ellipt

- `textwrap.shorten` from the standard library only cuts at the end and only between
  words: a single long word, or Chinese text without spaces, comes back as the bare
  placeholder `[...]`. It also collapses runs of whitespace even when the text fits, and
  it counts code points only.
- Plain slicing counts code points, so it splits combining accents and emoji sequences,
  overflows a terminal with wide characters and can exceed a byte limit.
- `wcwidth.clip` cuts by terminal columns but adds no marker, and pads a wide character
  it splits with a space.

`ellipt` cuts where you ask, in the unit you need, at grapheme cluster boundaries, and
tells you what it removed. The rules, the Unicode sources and the edge cases are in the
[guide](https://github.com/JaviLianes8/ellipt/blob/main/GUIDE.md); every release is
described in the [changelog](https://github.com/JaviLianes8/ellipt/blob/main/CHANGELOG.md).

## License

MIT, see [LICENSE](https://github.com/JaviLianes8/ellipt/blob/main/LICENSE). The
embedded Unicode data is covered by the Unicode License v3, see
[LICENSE-UNICODE](https://github.com/JaviLianes8/ellipt/blob/main/LICENSE-UNICODE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
