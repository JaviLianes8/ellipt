"""Run the examples written in the public docstrings."""

from __future__ import annotations

import doctest
import inspect
import re

import ellipt


def test_docstring_examples_pass() -> None:
    # Public objects report the package as their module, so doctest finds them all there.
    result = doctest.testmod(ellipt, optionflags=doctest.ELLIPSIS)
    assert result.failed == 0
    assert result.attempted >= 30


def test_every_public_name_has_a_runnable_example() -> None:
    assert ">>>" in (ellipt.__doc__ or "")
    for name in ellipt.__all__:
        value = getattr(ellipt, name)
        if inspect.isclass(value) or inspect.isfunction(value):
            assert ">>>" in (value.__doc__ or ""), name


def test_every_public_member_of_truncation_has_a_runnable_example() -> None:
    for name, member in vars(ellipt.Truncation).items():
        if name.startswith("_") and name != "__str__":
            continue
        if isinstance(member, property) or inspect.isfunction(member):
            assert ">>>" in (member.__doc__ or ""), name


def test_the_constants_are_shown_in_the_package_docstring() -> None:
    examples = [line for line in (ellipt.__doc__ or "").splitlines() if line.startswith(">>> ")]
    for name in ("ELLIPSIS", "UNITS", "UNICODE_VERSION", "Unit", "Where"):
        assert any(re.search(rf"\b{name}\b", line) for line in examples), name
