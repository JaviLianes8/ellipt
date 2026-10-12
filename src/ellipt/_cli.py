"""Command line tool: truncate every line of standard input or of the given files."""

from __future__ import annotations

import argparse
import contextlib
import errno
import os
import sys
from collections.abc import Iterator, Sequence
from typing import IO, NoReturn

from . import __version__
from ._core import ELLIPSIS, truncate
from ._measure import UNITS
from ._path import shorten_path

EXAMPLES = """\
examples:
  ls | ellipt 20                         end ellipsis at 20 columns
  ellipt 30 --where middle notes.txt     keep both ends of each line
  git ls-files | ellipt 28 --path        keep the root and the file name
  ellipt 255 --unit bytes --marker "" < titles.txt
                                         fit a 255-byte UTF-8 column
  tail -f app.log | ellipt 80 --where start --ellipsis

Lines are read as UTF-8 (a leading byte order mark is dropped) and written as UTF-8,
keeping each LF or CRLF line ending. The limit counts the marker, and no grapheme
cluster (accent, flag, emoji sequence) is ever split. With --unit columns, tabs are
expanded to spaces first (--tabsize); ANSI escape sequences are not recognised, so
strip colours before piping. Errors go to standard error with exit status 1.
"""


class _PipeClosed(Exception):
    """The reader of standard output went away."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def _non_negative(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a whole number: {value!r}") from None
    if number < 0:
        raise argparse.ArgumentTypeError(f"must be non-negative: {number}")
    return number


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser of the ``ellipt`` command."""
    parser = _Parser(
        prog="ellipt",
        description="Truncate each input line to LIMIT with an ellipsis at the start, "
        "middle or end.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("limit", type=_non_negative, metavar="LIMIT", help="maximum size")
    parser.add_argument("files", nargs="*", metavar="FILE", help="input files (default: stdin)")
    parser.add_argument(
        "-w", "--where", choices=("start", "middle", "end"), help="where to cut (default: end)"
    )
    parser.add_argument(
        "-u",
        "--unit",
        choices=UNITS,
        default="columns",
        help="what LIMIT counts (default: columns, terminal cells)",
    )
    marker = parser.add_mutually_exclusive_group()
    marker.add_argument("-m", "--marker", default="...", help='replacement text (default: "...")')
    marker.add_argument(
        "-e",
        "--ellipsis",
        dest="marker",
        action="store_const",
        const=ELLIPSIS,
        help="use the single character U+2026 HORIZONTAL ELLIPSIS as the marker",
    )
    parser.add_argument("--words", action="store_true", help="cut at whitespace when possible")
    parser.add_argument(
        "--path", action="store_true", help="treat lines as paths: drop middle directories"
    )
    parser.add_argument(
        "--ambiguous",
        type=int,
        choices=(1, 2),
        default=1,
        help="columns of East Asian Ambiguous characters (default: 1)",
    )
    parser.add_argument(
        "--tabsize",
        type=_non_negative,
        default=8,
        help="with --unit columns, expand tabs to this tab stop first; 0 keeps them as "
        "zero-width characters (default: 8)",
    )
    parser.add_argument("-V", "--version", action="version", version=f"ellipt {__version__}")
    return parser


def _lines(names: Sequence[str]) -> Iterator[tuple[str, int, bytes]]:
    """Yield ``(source name, line number, raw line)`` with any UTF-8 BOM removed."""
    if not names:
        yield from _numbered("<stdin>", sys.stdin.buffer)
        return
    for name in names:
        with open(name, "rb") as handle:
            yield from _numbered(name, handle)


def _numbered(name: str, handle: IO[bytes]) -> Iterator[tuple[str, int, bytes]]:
    for number, raw in enumerate(handle, 1):
        yield name, number, raw[3:] if number == 1 and raw.startswith(b"\xef\xbb\xbf") else raw


def _write(out: IO[bytes], data: bytes) -> None:
    try:
        out.write(data)
    except OSError as exc:
        # Windows reports a closed pipe as EINVAL rather than EPIPE.
        if isinstance(exc, BrokenPipeError) or exc.errno in (errno.EPIPE, errno.EINVAL):
            raise _PipeClosed from None
        raise


def _split_ending(line: str) -> tuple[str, str]:
    for ending in ("\r\n", "\n", "\r"):
        if line.endswith(ending):
            return line[: -len(ending)], ending
    return line, ""


def _run(args: argparse.Namespace, out: IO[bytes]) -> None:
    for name, number, raw in _lines(args.files):
        try:
            line = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"{name}: line {number} is not valid UTF-8: {exc.reason}") from None
        body, ending = _split_ending(line)
        if args.unit == "columns" and args.tabsize and "\t" in body:
            body = body.expandtabs(args.tabsize)
        if args.path:
            short = shorten_path(
                body, args.limit, unit=args.unit, marker=args.marker, ambiguous=args.ambiguous
            )
        else:
            short = truncate(
                body,
                args.limit,
                where=args.where or "end",
                unit=args.unit,
                marker=args.marker,
                words=args.words,
                ambiguous=args.ambiguous,
            ).text
        _write(out, (short + ending).encode("utf-8"))


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line tool and return its exit status."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.path and (args.where not in (None, "middle") or args.words):
        parser.error("--path always cuts in the middle and does not take --words")
    try:
        _run(args, sys.stdout.buffer)
        _write(sys.stdout.buffer, b"")
        sys.stdout.flush()
    except (_PipeClosed, BrokenPipeError):
        # Point stdout at the null device so the flush at exit cannot fail again.
        with contextlib.suppress(OSError, ValueError, AttributeError):
            null = os.open(os.devnull, os.O_WRONLY)
            os.dup2(null, sys.stdout.fileno())
            os.close(null)
        return 0
    except (OSError, ValueError) as exc:
        print(f"ellipt: error: {exc}", file=sys.stderr)
        return 1
    return 0
