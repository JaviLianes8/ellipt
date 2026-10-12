"""Display width (UAX #11 East Asian Width plus emoji presentation) of clusters and text."""

from __future__ import annotations

from ._props import AMBIGUOUS, EMOJI_BIT, EXT_PICT_BIT, GCB, MODIFIER_BIT, WIDTH_SHIFT, prop

_RI = GCB["Regional_Indicator"]
_VS15 = "\ufe0e"
_VS16 = "\ufe0f"
_ZWJ = "\u200d"
_TAGS = range(0xE0020, 0xE0080)


def check_ambiguous(ambiguous: int) -> int:
    """Return ``ambiguous`` after checking it is 1 or 2."""
    if isinstance(ambiguous, bool) or ambiguous not in (1, 2):
        raise ValueError(f"ambiguous must be 1 or 2, not {ambiguous!r}")
    return ambiguous


def _code_width(code: int, ambiguous: int) -> int:
    width = code >> WIDTH_SHIFT
    return ambiguous if width == AMBIGUOUS else width


def cluster_width(cluster: str, ambiguous: int = 1) -> int:
    """Return the display width of one extended grapheme cluster.

    Emoji sequences draw as one glyph: an emoji with VS16, a skin tone modifier, a ZWJ
    sequence, a tag sequence or a regional indicator pair (a flag) is two cells and an
    emoji with VS15 is one. Any other cluster is the sum of its code points.
    """
    code = prop(ord(cluster[0]))
    if len(cluster) == 1:
        return _code_width(code, ambiguous)
    rest = cluster[1:]
    if code & EMOJI_BIT and not code & MODIFIER_BIT:
        if _VS15 in rest:
            return 1
        if _VS16 in rest:
            return 2
    if (
        code & (EMOJI_BIT | EXT_PICT_BIT)
        and not code & MODIFIER_BIT
        and (_ZWJ in rest or any(prop(ord(ch)) & MODIFIER_BIT or ord(ch) in _TAGS for ch in rest))
    ):
        return 2
    if code & 0x0F == _RI and prop(ord(rest[0])) & 0x0F == _RI:
        return 2
    return sum(_code_width(prop(ord(ch)), ambiguous) for ch in cluster)
