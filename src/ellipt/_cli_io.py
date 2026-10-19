"""Reading, cutting and writing lines for the command line tool."""

from __future__ import annotations

import argparse
import errno
from collections.abc import Iterator, Sequence
from typing import IO

from ._core import truncate
from ._measure import clusters
from ._path import shorten_path
from ._width import cluster_width


class PipeClosed(Exception):
    """The reader of standard output went away."""


def lines(names: Sequence[str], stdin: IO[bytes] | None) -> Iterator[tuple[str, int, bytes]]:
    """Yield ``(source name, line number, raw line)`` with any UTF-8 BOM removed."""
    if not names:
        if stdin is None:
            raise OSError("standard input is closed")
        yield from _numbered("<stdin>", stdin)
        return
    for name in names:
        with open(name, "rb") as handle:
            yield from _numbered(name, handle)


def _numbered(name: str, handle: IO[bytes]) -> Iterator[tuple[str, int, bytes]]:
    for number, raw in enumerate(handle, 1):
        yield name, number, raw[3:] if number == 1 and raw.startswith(b"\xef\xbb\xbf") else raw


def write(out: IO[bytes], data: bytes | None = None) -> None:
    """Write ``data`` (or flush when it is None), turning a closed pipe into ``PipeClosed``."""
    try:
        if data is None:
            out.flush()
        else:
            out.write(data)
    except OSError as exc:
        # Windows reports a closed pipe as EINVAL rather than EPIPE.
        if isinstance(exc, BrokenPipeError) or exc.errno in (errno.EPIPE, errno.EINVAL):
            raise PipeClosed from None
        raise


def split_ending(line: str) -> tuple[str, str]:
    """Split a line into its body and its CRLF, LF or CR ending."""
    for ending in ("\r\n", "\n", "\r"):
        if line.endswith(ending):
            return line[: -len(ending)], ending
    return line, ""


def expand_tabs(text: str, tabsize: int, ambiguous: int) -> str:
    """Replace each tab with spaces up to the next multiple of ``tabsize`` display columns.

    Columns are counted the way ``measure(..., "columns")`` counts them, so a wide
    character before a tab takes two of the columns; a CR or LF starts a new line.
    """
    out: list[str] = []
    column = 0
    for cluster in clusters(text):
        if cluster == "\t":
            pad = tabsize - column % tabsize
            out.append(" " * pad)
            column += pad
        elif cluster in ("\r", "\n", "\r\n"):
            out.append(cluster)
            column = 0
        else:
            out.append(cluster)
            column += cluster_width(cluster, ambiguous)
    return "".join(out)


def cut_line(args: argparse.Namespace, body: str) -> str:
    """Shorten one line body as the command line options ask."""
    if args.path:
        return shorten_path(
            body, args.limit, unit=args.unit, marker=args.marker, ambiguous=args.ambiguous
        )
    return truncate(
        body,
        args.limit,
        where=args.where or "end",
        unit=args.unit,
        marker=args.marker,
        words=args.words,
        ambiguous=args.ambiguous,
    ).text


def run(args: argparse.Namespace, out: IO[bytes], stdin: IO[bytes] | None) -> None:
    """Shorten every input line and write it with its own line ending."""
    for name, number, raw in lines(args.files, stdin):
        try:
            line = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"{name}: line {number} is not valid UTF-8: {exc.reason}") from None
        body, ending = split_ending(line)
        if args.unit == "columns" and args.tabsize and "\t" in body:
            body = expand_tabs(body, args.tabsize, args.ambiguous)
        write(out, (cut_line(args, body) + ending).encode("utf-8"))
