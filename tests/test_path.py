"""Path-aware middle truncation."""

from __future__ import annotations

import pytest

from ellipt import ELLIPSIS, measure, shorten_path

POSIX = "/home/me/projects/app/src/main.py"


def test_a_fitting_path_is_unchanged() -> None:
    assert shorten_path(POSIX, len(POSIX)) == POSIX


@pytest.mark.parametrize(
    ("limit", "expected"),
    [
        (32, "/.../me/projects/app/src/main.py"),
        (31, "/.../projects/app/src/main.py"),
        (28, "/.../app/src/main.py"),
        (20, "/.../app/src/main.py"),
        (19, "/.../src/main.py"),
        (15, "/.../main.py"),
        (11, ".../main.py"),
        (7, "main.py"),
        (6, "ma...y"),
    ],
)
def test_directories_go_first_then_the_root_then_the_name(limit: int, expected: str) -> None:
    assert shorten_path(POSIX, limit) == expected


def test_windows_paths_keep_the_drive() -> None:
    path = r"C:\Users\me\AppData\Local\Temp\build.log"
    assert shorten_path(path, 24) == "C:\\...\\Temp\\build.log"
    # With "/" as the only separator the whole path is one name, cut in its stem.
    assert shorten_path(path, 24, sep="/") == "C:\\Users\\...mp\\build.log"


def test_relative_paths_keep_the_top_directory() -> None:
    assert shorten_path("src/pkg/sub/deep/mod.py", 18, marker=ELLIPSIS) == "src/\u2026/deep/mod.py"


def test_a_long_file_name_keeps_its_extension() -> None:
    name = "quarterly_financial_report_final_v2.xlsx"
    result = shorten_path("docs/" + name, 20)
    assert result.endswith(".xlsx") and "..." in result and len(result) <= 20


def test_a_name_without_a_usable_extension_is_cut_in_the_middle() -> None:
    assert shorten_path("abcdefghijklmnop", 9) == "abc...nop"
    assert shorten_path(".bashrc_extremely_long", 9) == ".ba...ong"


def test_a_trailing_separator_stays_with_the_last_directory() -> None:
    assert shorten_path("/srv/www/site/public/", 16) == "/.../public/"


def test_columns_unit_keeps_wide_names_within_the_limit() -> None:
    path = "/data/\u5199\u771f/\u65c5\u884c/\u5bcc\u58eb\u5c71\u306e\u5199\u771f.jpg"
    result = shorten_path(path, 16, unit="columns", marker=ELLIPSIS)
    assert measure(result, "columns") <= 16 and result.endswith(".jpg")


def test_unc_and_double_slash_roots_keep_host_and_share() -> None:
    unc = "\\\\server\\share\\dir\\sub\\file.txt"
    assert shorten_path(unc, 30) == "\\\\server\\share\\...\\file.txt"
    assert shorten_path("//host/share/a/b/c/d.txt", 23) == "//host/share/.../d.txt"


def test_compound_extensions_stay_together() -> None:
    assert shorten_path("/x/" + "n" * 30 + ".tar.gz", 15) == "nnn...nn.tar.gz"


def test_bad_separator_and_empty_marker_are_rejected_even_when_the_path_fits() -> None:
    with pytest.raises(ValueError, match="single character"):
        shorten_path("ab", 10, sep="//")
    with pytest.raises(ValueError, match="must not be empty"):
        shorten_path("ab", 10, marker="")
