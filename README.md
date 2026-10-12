# ellipt

Truncate strings with an ellipsis at the start, middle or end. The limit can count code
points, grapheme clusters, terminal columns or UTF-8 bytes, the marker is counted inside
the limit, and the cut never splits an accent, a flag or an emoji sequence. Typed, zero
dependencies, Unicode 18.0.0 tables embedded.

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
$ printf 'hello world\n' | ellipt 8
hello...
$ git ls-files | ellipt 28 --path
$ ellipt 30 --where middle --ellipsis notes.txt
$ ellipt 255 --unit bytes --marker "" < titles.txt
```

The command reads standard input (or the files given) as UTF-8, keeps each LF or CRLF
line ending, and counts terminal columns by default, expanding tabs to 8-column stops
first (`--tabsize`). `--ellipsis` uses U+2026 as the marker without having to type it.
`ellipt --help` lists every option. Errors go to standard error with exit status 1, and
a reader that stops early (`| head`) is not an error.

## Why

`textwrap.shorten` only cuts at the end, collapses whitespace and always cuts on words.
Plain slicing (`s[:n] + "..."`) splits emoji and accents, overflows a terminal with wide
characters and can exceed a byte limit. `ellipt` cuts where you ask, in the unit you
need, and guarantees the result is never longer than the limit. See [GUIDE.md](GUIDE.md)
for the exact rules, the Unicode sources and the edge cases.

## License

MIT. See [LICENSE](LICENSE). The embedded Unicode data is covered by the Unicode
License v3, see [LICENSE-UNICODE](LICENSE-UNICODE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
