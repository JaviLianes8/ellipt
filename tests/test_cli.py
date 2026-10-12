"""The ellipt command, driven in process with real byte streams."""

from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ellipt import __version__
from ellipt._cli import main

WORLD = "\u4f60\u597d\u4e16\u754c"  # four wide characters, 8 columns


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
        (["5", "-m", "\u2026"], WORLD + "\n", "\u4f60\u597d\u2026\n"),
        (["5", "-u", "chars", "-m", "\u2026"], WORLD + "\n", WORLD + "\n"),
        (["6", "-u", "bytes", "-m", ""], "\u00e9\u00e9\u00e9\u00e9\n", "\u00e9\u00e9\u00e9\n"),
        (["12", "--words"], "The quick brown fox\n", "The quick...\n"),
        (["19", "--path"], "/home/me/projects/app/src/main.py\n", "/.../src/main.py\n"),
        (["4", "--ambiguous", "2", "-m", ""], "\u2500\u2500\u2500\n", "\u2500\u2500\n"),
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


@pytest.mark.parametrize(
    ("args", "data", "expected"),
    [
        (["4", "-e"], "abcdef\n", "abc\u2026\n"),
        (["12", "-e"], "a\tbcdefghijk\n", "a       bcd\u2026\n"),
        (["12", "-e", "--tabsize", "4"], "a\tbcdefghijk\n", "a   bcdefgh\u2026\n"),
        (["4", "-e", "--tabsize", "0"], "a\tbcdef\n", "a\tbc\u2026\n"),
        (["4", "-e", "-u", "chars"], "a\tbcdef\n", "a\tb\u2026\n"),
        (["5"], "\ufeffabcdefgh\nij\n", "ab...\nij\n"),
    ],
)
def test_ellipsis_flag_tabs_and_bom(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    args: list[str],
    data: str,
    expected: str,
) -> None:
    assert _run(monkeypatch, capsys, args, data) == (0, expected, "")


def test_marker_and_ellipsis_are_exclusive(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exited:
        main(["4", "-e", "-m", "~"])
    assert exited.value.code == 1 and "not allowed" in capsys.readouterr().err


def test_a_decoding_error_names_the_file_and_its_own_line_number(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    good, bad = tmp_path / "good.txt", tmp_path / "bad.txt"
    good.write_bytes(b"one\ntwo\n")
    bad.write_bytes(b"ok\n\xff\n")
    monkeypatch.setattr(sys, "stdout", _Stream())
    assert main(["5", str(good), str(bad)]) == 1
    assert f"{bad}: line 2 is not valid UTF-8" in capsys.readouterr().err


def test_a_reader_that_stops_early_is_not_an_error(tmp_path: Path) -> None:
    source = tmp_path / "big.txt"
    source.write_bytes(b"some long line of text\n" * 200_000)
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent / "src")
    command = [sys.executable, "-m", "ellipt", "10", str(source)]
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env) as proc:
        assert proc.stdout is not None and proc.stderr is not None
        first = proc.stdout.readline()
        proc.stdout.close()
        err = proc.stderr.read()
        code = proc.wait(timeout=60)
    assert first == b"some lo...\n"
    assert (code, err) == (0, b"")
