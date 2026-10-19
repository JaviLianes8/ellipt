"""Edge contracts added after the author mutation round found them unpinned."""

from __future__ import annotations

import io
import sys

import pytest

from ellipt import measure, shorten_path, truncate
from ellipt._cli import main


def test_an_emoji_with_vs15_is_one_column_and_with_vs16_two() -> None:
    for emoji in ("\u2764", "\U0001f600", "\u263a"):
        assert measure(emoji + "\ufe0e", "columns") == 1
        assert measure(emoji + "\ufe0f", "columns") == 2


@pytest.mark.parametrize(
    ("path", "limit", "expected"),
    [
        ("/aaa/bbb/ccc/ddd/", 13, "/.../ccc/ddd/"),
        ("/aaa/bbb/ccc/ddd/", 8, ".../ddd/"),
        ("/aaa/bbb/ccc/ddd//", 9, ".../ddd//"),
        ("/aaa/bbb/ccc/ddd/", 4, "ddd/"),
        ("aaa/bbb/", 7, "bbb/"),
    ],
)
def test_trailing_separators_stay_with_the_last_directory(
    path: str, limit: int, expected: str
) -> None:
    assert shorten_path(path, limit) == expected


@pytest.mark.parametrize(
    ("text", "limit", "expected"),
    [
        ("aa\u4f60", 3, "aa."),
        ("\u4f60a\u4f60", 4, "\u4f60a."),
        ("a \u4f60", 3, "a ."),
    ],
)
def test_middle_hands_budget_the_tail_cannot_use_back_to_the_head(
    text: str, limit: int, expected: str
) -> None:
    result = truncate(text, limit, where="middle", unit="columns", marker=".")
    assert result.text == expected and result.tail == ""


class _Stream:
    def __init__(self, data: bytes = b"") -> None:
        self.buffer = io.BytesIO(data)

    def flush(self) -> None:
        pass


@pytest.mark.parametrize(
    ("args", "data", "expected"),
    [
        (["8", "-u", "chars"], b"hello world\r\nhello world\n", b"hello...\r\nhello...\n"),
        (["4", "-u", "chars", "-m", ""], b"abcdef\r", b"abcd\r"),
        (["10"], "\ufeffab\n\ufeffcd\n".encode(), "ab\n\ufeffcd\n".encode()),
    ],
)
def test_line_endings_are_kept_and_only_the_first_bom_is_dropped(
    monkeypatch: pytest.MonkeyPatch, args: list[str], data: bytes, expected: bytes
) -> None:
    out = _Stream()
    monkeypatch.setattr(sys, "stdin", _Stream(data))
    monkeypatch.setattr(sys, "stdout", out)
    assert main(args) == 0
    assert out.buffer.getvalue() == expected
