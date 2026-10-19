"""Usage errors of the command: exit status 2, short messages, nothing read or written."""

from __future__ import annotations

import io
import sys

import pytest

from ellipt._cli import MESSAGE_LIMIT, main


class _Stream:
    def __init__(self, data: bytes = b"") -> None:
        self.buffer = io.BytesIO(data)

    def flush(self) -> None:
        pass


HUGE = 100_000


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["9" * HUGE], "too large"),
        (["-" + "9" * HUGE], "too large"),
        (["x" * HUGE], "not a whole number"),
        (["5", "--unit", "u" * HUGE], "invalid choice"),
        (["5", "--ambiguous", "9" * HUGE], "--ambiguous"),
        (["5", "--where", "w" * HUGE], "invalid choice"),
        (["5", "--tabsize", "9" * HUGE], "too large"),
        (["5", "-m", "m" * HUGE], "does not fit"),
        (["5", "--path", "-m", "m" * HUGE], "does not fit"),
    ],
)
def test_huge_arguments_give_a_bounded_usage_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    args: list[str],
    message: str,
) -> None:
    out = _Stream()
    monkeypatch.setattr(sys, "stdin", None)
    monkeypatch.setattr(sys, "stdout", out)
    with pytest.raises(SystemExit) as exited:
        main(args)
    err = capsys.readouterr().err
    assert exited.value.code == 2 and message in err
    last = err.splitlines()[-1]
    assert last.startswith("ellipt: error: ")
    assert len(last) <= len("ellipt: error: ") + MESSAGE_LIMIT + 3
    assert out.buffer.getvalue() == b""


def test_input_errors_exit_1_and_usage_errors_exit_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdout", _Stream())
    monkeypatch.setattr(sys, "stdin", _Stream(b"ok\n\xc3\n"))
    assert main(["5"]) == 1
    assert capsys.readouterr().err == (
        "ellipt: error: <stdin>: line 2 is not valid UTF-8: invalid continuation byte\n"
    )
    monkeypatch.setattr(sys, "stdin", _Stream(b"hello\n"))
    with pytest.raises(SystemExit) as exited:
        main(["2"])
    assert exited.value.code == 2


def test_an_empty_input_with_a_limit_too_small_is_still_a_usage_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "stdin", _Stream(b""))
    monkeypatch.setattr(sys, "stdout", _Stream())
    with pytest.raises(SystemExit) as exited:
        main(["2"])
    assert exited.value.code == 2


def test_a_closed_standard_input_or_output_is_reported(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", None)
    monkeypatch.setattr(sys, "stdout", _Stream())
    assert main(["5"]) == 1
    assert capsys.readouterr().err == "ellipt: error: standard input is closed\n"
    monkeypatch.setattr(sys, "stdout", None)
    assert main(["5"]) == 1
    assert capsys.readouterr().err == "ellipt: error: standard output is closed\n"
