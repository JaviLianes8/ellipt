"""Command line tool: truncate every line of standard input or of the given files."""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
from collections.abc import Sequence
from typing import NoReturn

from . import __version__
from ._checks import UNITS, WHERES
from ._cli_io import PipeClosed, cut_line, run, write
from ._core import ELLIPSIS

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
expanded to spaces first (--tabsize stops, wide characters count as two columns);
ANSI escape sequences are not recognised, so strip colours before piping.
Exit status: 0 on success (also when the reader stops early, as with | head),
1 when an input cannot be read or is not UTF-8, 2 for a usage error, such as
a marker that does not fit in LIMIT.
"""

# argparse quotes the offending argument whole; a message is cut to this length.
MESSAGE_LIMIT = 300


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        if len(message) > MESSAGE_LIMIT:
            message = message[:MESSAGE_LIMIT] + "..."
        if sys.stderr is not None:
            self.print_usage(sys.stderr)
            print(f"{self.prog}: error: {message}", file=sys.stderr)
        raise SystemExit(2)


def _non_negative(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        shown = value if len(value) <= 40 else value[:40] + "..."
        digits = value.strip().lstrip("+-").replace("_", "")
        problem = "too large" if digits.isdigit() else "not a whole number"
        raise argparse.ArgumentTypeError(f"{problem}: {shown!r}") from None
    if number < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
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
    parser.add_argument("-w", "--where", choices=WHERES, help="where to cut (default: end)")
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


def _check(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    """Reject option combinations before any input is read."""
    if args.path and (args.where not in (None, "middle") or args.words):
        parser.error("--path always cuts in the middle and does not take --words")
    try:
        args.marker.encode("utf-8")
    except UnicodeEncodeError:
        parser.error("the marker is not valid UTF-8 text")
    try:
        cut_line(args, "")  # the library checks every option against LIMIT
    except ValueError as exc:
        parser.error(str(exc))


def _report(message: str) -> int:
    if sys.stderr is not None:
        print(f"ellipt: error: {message}", file=sys.stderr)
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line tool and return its exit status."""
    parser = build_parser()
    args = parser.parse_args(argv)
    _check(parser, args)
    out = getattr(sys.stdout, "buffer", None)
    if out is None:
        return _report("standard output is closed")
    try:
        run(args, out, getattr(sys.stdin, "buffer", None))
        write(out)
    except PipeClosed:
        # Point stdout at the null device so the flush at exit cannot fail again.
        with contextlib.suppress(OSError, ValueError, AttributeError):
            null = os.open(os.devnull, os.O_WRONLY)
            os.dup2(null, sys.stdout.fileno())
            os.close(null)
        return 0
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError) as exc:
        return _report(str(exc))
    return 0
