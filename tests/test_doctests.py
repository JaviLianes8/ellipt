"""Run the examples written in the public docstrings."""

from __future__ import annotations

import doctest
import importlib

import pytest

MODULES = [
    "ellipt._core",
    "ellipt._measure",
    "ellipt._graphemes",
    "ellipt._path",
    "ellipt._shorten",
]


@pytest.mark.parametrize("name", MODULES)
def test_docstring_examples(name: str) -> None:
    result = doctest.testmod(importlib.import_module(name))
    assert result.attempted > 0
    assert result.failed == 0
