"""The ellipt command, driven in process with real byte streams."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

from ellipt import __version__
from ellipt._cli import main


class _Stream:
    def __init__(self, data: bytes = b"") -> None:
        self.buffer = io.BytesIO(data)

    def flush(self) -> None:
        pass


def _run(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], args: list[str], data: str
) -> tuple[int, str, str]:
    out = _Stream()
    monkeypatch.setattr(sys, "stdin", _Stream(data.encode("utf-8")))
    monkeypatch.setattr(sys, "stdout", out)
    code = main(args)
    return code, out.buffer.getvalue().decode("utf-8"), capsys.readouterr().err


@pytest.mark.parametrize(
    ("args", "data", "expected"),
    [
        (["8"], "hello world\nok\n", "hello...\nok\n"),
        (["8", "-w", "start"], "hello world\r\n", "...world\r\n"),
        (["9", "--where", "middle"], "hello world", "hel...rld"),
        (["5", "-m", "…"], "你好世界\n", "你好…\n"),
        (["5", "-u", "chars", "-m", "…"], "你好世界\n", "你好世界\n"),
        (["6", "-u", "bytes", "-m", ""], "éééé\n", "ééé\n"),
        (["12", "--words"], "The quick brown fox\n", "The quick...\n"),
        (["19", "--path"], "/home/me/projects/app/src/main.py\n", "/.../src/main.py\n"),
        (["4", "--ambiguous", "2", "-m", ""], "───\n", "──\n"),
        (["3"], "", ""),
    ],
)  # fmt: skip
def test_lines_are_truncated(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    args: list[str],
    data: str,
    expected: str,
) -> None:
    assert _run(monkeypatch, capsys, args, data) == (0, expected, "")


def test_files_are_read_in_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    first, second = tmp_path / "a.txt", tmp_path / "b.txt"
    first.write_bytes(b"abcdefgh\n")
    second.write_bytes(b"12345678")
    code, out, _ = _run(monkeypatch, capsys, ["5", str(first), str(second)], "")
    assert (code, out) == (0, "ab...\n12...")


@pytest.mark.parametrize(
    ("args", "data", "message"),
    [
        (["2"], "hello\n", "does not fit"),
        (["-1"], "x\n", "non-negative"),
        (["ten"], "x\n", "not a whole number"),
        (["5", "--path", "--words"], "x\n", "--path"),
        (["5", "--path", "-w", "end"], "x\n", "--path"),
        (["5", "-u", "pixels"], "x\n", "invalid choice"),
        (["5", "missing-file.txt"], "", "missing-file.txt"),
    ],
)
def test_errors_go_to_stderr_with_status_1(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    args: list[str],
    data: str,
    message: str,
) -> None:
    try:
        code, out, err = _run(monkeypatch, capsys, args, data)
    except SystemExit as exc:
        code, out, err = int(str(exc.code)), "", capsys.readouterr().err
    assert code == 1 and out == "" and message in err


def test_invalid_utf8_is_an_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", _Stream(b"\xff\xfe\n"))
    monkeypatch.setattr(sys, "stdout", _Stream())
    assert main(["3"]) == 1
    assert "not valid UTF-8" in capsys.readouterr().err


def test_version_and_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exited:
        main(["--version"])
    assert exited.value.code == 0 and capsys.readouterr().out.strip() == f"ellipt {__version__}"
    with pytest.raises(SystemExit):
        main(["--help"])
    assert "examples:" in capsys.readouterr().out
