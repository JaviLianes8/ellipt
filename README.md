# ellipt

Truncate strings with an ellipsis at the start, middle or end, by character count or display width.

## Install

```
pip install ellipt
```

## Usage

```python
from ellipt import shorten

shorten("hello world", 8)                   # 'hello...'
shorten("hello world", 8, where="start")    # '...world'
shorten("hello world", 9, where="middle")   # 'hel...rld'
shorten("/var/log/app/service.log", 16, where="middle")  # '/var/lo...ce.log'

# Any marker you like.
shorten("hello world", 6, marker="_")       # 'hello_'

# Text that already fits is returned unchanged.
shorten("short", 20)                        # 'short'
```

By default the width is a code point count. Pass `width_aware=True` to measure in
display columns, so wide East Asian characters count as two and the result never
overflows a fixed-width layout:

```python
shorten("广广广x", 5, marker="..", width_aware=True)  # '广..'
```

A width too small to hold the marker, a negative width, or an unknown position
raises `ValueError`.

## Why

The standard library's `textwrap.shorten` only cuts at the end and collapses on
word boundaries, so it cannot trim the middle of a path or the head of an id, and
it never lands on an exact length. `ellipt` cuts at the start, middle or end at a
precise length, with a marker you choose, and can measure display width for
terminal and fixed-column output.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
