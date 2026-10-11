import pytest

from ellipt import shorten


def test_end_is_the_default_position() -> None:
    assert shorten("hello world", 8) == "hello..."


def test_end_keeps_the_prefix() -> None:
    assert shorten("hello world", 8, where="end") == "hello..."


def test_start_keeps_the_suffix() -> None:
    assert shorten("hello world", 8, where="start") == "...world"


def test_middle_keeps_both_ends() -> None:
    assert shorten("hello world", 9, where="middle") == "hel...rld"


def test_a_custom_marker_is_used() -> None:
    assert shorten("hello world", 6, marker="_") == "hello_"


def test_result_never_exceeds_the_width() -> None:
    for where in ("start", "middle", "end"):
        assert len(shorten("abcdefghij", 7, where=where)) <= 7


def test_a_string_shorter_than_width_is_unchanged() -> None:
    assert shorten("short", 20) == "short"


def test_a_string_of_exactly_width_is_unchanged() -> None:
    assert shorten("sixsix", 6) == "sixsix"


def test_a_marker_wider_than_width_is_rejected() -> None:
    with pytest.raises(ValueError, match="does not fit"):
        shorten("hello world", 2, marker="...")


def test_a_negative_width_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        shorten("hello", -1)


def test_an_unknown_position_is_rejected() -> None:
    with pytest.raises(ValueError, match="where must be"):
        shorten("hello world", 8, where="top")  # type: ignore[arg-type]


def test_width_aware_counts_wide_characters_as_two() -> None:
    result = shorten("广广广x", 5, marker="..", width_aware=True)
    assert result == "广.."


def test_width_aware_leaves_fitting_wide_text_unchanged() -> None:
    text = "广广"
    assert shorten(text, 4, width_aware=True) == text


def test_without_width_aware_wide_characters_count_as_one() -> None:
    text = "广广广"
    assert shorten(text, 4, width_aware=False) == text
