"""Behaviour of truncate, measure and the units, cluster by cluster."""

from __future__ import annotations

import pytest

from ellipt import ELLIPSIS, Truncation, measure, shorten, truncate

FAMILY = "\U0001f468\u200d\U0001f469\u200d\U0001f467"  # man ZWJ woman ZWJ girl
FLAG = "\U0001f1ea\U0001f1f8"  # regional indicators E S
E_ACUTE = "e\u0301"  # e + COMBINING ACUTE ACCENT


def test_a_fitting_text_is_reported_untouched() -> None:
    result = truncate("short", 10)
    assert result == Truncation("short", "short", "", "", "short", "chars", 10, 5)
    assert not result.truncated and result.removed == "" and result.removed_span == (5, 5)


def test_the_result_records_head_marker_tail_and_removed() -> None:
    result = truncate("abcdefghij", 7, where="middle")
    assert (result.head, result.marker, result.tail) == ("ab", "...", "ij")
    assert result.text == "ab...ij" == str(result)
    assert result.removed == "cdefgh" and result.removed_span == (2, 8)
    assert result.truncated and result.size == 7


def test_a_combining_accent_is_never_separated_from_its_letter() -> None:
    text = "caf" + E_ACUTE + " au lait"
    assert truncate(text, 6, marker="..").head == "caf"
    assert truncate(text, 7, marker="..").head == "caf" + E_ACUTE


def test_a_flag_and_a_zwj_family_are_kept_or_dropped_whole() -> None:
    assert shorten("ab" + FLAG + "cd", 5, marker="..") == "ab.."
    assert shorten(FAMILY + "xyz", 6, marker="..") == ".."
    assert truncate(FAMILY + "xyz", 7, marker="..").head == FAMILY
    assert truncate("xyz" + FAMILY, 6, where="start", marker="..").tail == ""


def test_units_measure_the_same_text_differently() -> None:
    text = "a" + FAMILY + "\u4e16"
    assert measure(text) == 7
    assert measure(text, "graphemes") == 3
    assert measure(text, "columns") == 5
    assert measure(text, "bytes") == 1 + 18 + 3


def test_graphemes_unit_counts_what_a_reader_sees() -> None:
    assert shorten(E_ACUTE * 5, 4, unit="graphemes", marker=ELLIPSIS) == E_ACUTE * 3 + ELLIPSIS


def test_columns_unit_counts_wide_characters_as_two() -> None:
    assert shorten("\u4f60\u597d\u4e16\u754c", 5, unit="columns", marker=ELLIPSIS) == (
        "\u4f60\u597d" + ELLIPSIS
    )
    assert shorten("\u2500" * 4, 3, unit="columns", ambiguous=2, marker="") == "\u2500"


def test_bytes_unit_fits_a_utf8_column() -> None:
    result = truncate("na\u00efve caf\u00e9 cr\u00e8me", 12, unit="bytes", marker=ELLIPSIS)
    assert result.text.encode() == "na\u00efve ca\u2026".encode()
    assert len(result.text.encode()) <= 12


def test_the_unicode_ellipsis_is_cheaper_than_three_dots_except_in_bytes() -> None:
    for unit in ("chars", "graphemes", "columns"):
        assert measure(ELLIPSIS, unit) == 1 and measure("...", unit) == 3
    assert measure(ELLIPSIS, "bytes") == measure("...", "bytes") == 3


def test_width_aware_is_the_columns_unit() -> None:
    text = "\u5e7f\u5e7f\u5e7fx"
    assert shorten(text, 5, width_aware=True) == shorten(text, 5, unit="columns")
    with pytest.raises(ValueError, match="conflicts"):
        shorten(text, 5, width_aware=True, unit="bytes")


def test_middle_hands_leftover_budget_to_the_right() -> None:
    # The left half (2 columns) stops before the wide character; its spare column goes right.
    result = truncate("a\u4f60bcdefgh", 5, where="middle", unit="columns", marker=".")
    assert (result.head, result.tail, result.size) == ("a", "fgh", 5)


def test_words_backs_off_to_whitespace_and_trims_it() -> None:
    text = "The quick brown fox jumps"
    assert shorten(text, 14, words=True, marker=ELLIPSIS) == "The quick" + ELLIPSIS
    assert shorten(text, 14, marker=ELLIPSIS) == "The quick bro" + ELLIPSIS
    assert shorten(text, 12, where="start", words=True, marker=ELLIPSIS) == ELLIPSIS + "fox jumps"
    middle = shorten(text, 16, where="middle", words=True, marker=ELLIPSIS)
    assert middle == "The" + ELLIPSIS + "fox jumps"


def test_words_in_the_middle_reuses_the_budget_a_snap_frees() -> None:
    assert shorten("a b c d e f", 7, where="middle", words=True) == "a...e f"


def test_words_ignores_trailing_whitespace_instead_of_cutting_a_word() -> None:
    assert shorten("alpha beta gamma ", 12, where="middle", words=True) == "alpha..."
    assert shorten("word " * 5, 12, where="middle", words=True) == "word...word "


def test_words_falls_back_to_a_hard_cut_for_one_long_word() -> None:
    assert shorten("Supercalifragilistic", 8, words=True) == "Super..."


def test_a_zero_limit_works_with_an_empty_marker() -> None:
    assert truncate("abc", 0, marker="").text == ""
    assert truncate("", 0, marker="").text == ""


def test_the_marker_must_fit_even_when_the_text_does() -> None:
    # Like textwrap.shorten: a limit that cannot hold the marker is an error for any text.
    with pytest.raises(ValueError, match="marker of size 3 does not fit in limit 0"):
        truncate("", 0)
    with pytest.raises(ValueError, match="marker of size 3 does not fit in limit 2"):
        shorten("hi", 2)


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"limit": -1}, ValueError, "non-negative"),
        ({"limit": 2}, ValueError, "does not fit"),
        ({"limit": 5, "where": "top"}, ValueError, "where must be"),
        ({"limit": 5, "unit": "pixels"}, ValueError, "unit must be"),
        ({"limit": 5, "ambiguous": 3}, ValueError, "ambiguous must be"),
        ({"limit": 5.0}, TypeError, "limit must be int"),
        ({"limit": True}, TypeError, "limit must be int"),
        ({"limit": 5, "marker": None}, TypeError, "marker must be str"),
    ],
)
def test_bad_arguments_are_rejected(kwargs: dict[str, object], error: type, match: str) -> None:
    with pytest.raises(error, match=match):
        truncate("hello world", **kwargs)  # type: ignore[arg-type]


def test_non_string_text_is_rejected() -> None:
    with pytest.raises(TypeError, match="text must be str"):
        truncate(b"bytes", 3)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="text must be str"):
        measure(None)  # type: ignore[arg-type]


def test_a_marker_that_would_merge_with_the_head_still_respects_the_limit() -> None:
    # VS16 turns a narrow heart into a wide emoji; the engine re-measures and backs off.
    result = truncate("\u2764abc", 3, unit="columns", marker="\ufe0f.")
    assert result.size <= 3 and result.text.startswith(result.head)
