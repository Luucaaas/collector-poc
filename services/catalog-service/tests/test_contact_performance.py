"""Regression for Sonar python:S8786: contact details detection runs in linear time."""

import time

import pytest

from catalog.contact import contact_reasons

# Worst-case texts: long runs without « @ », alternating digits and separators.
WORST_CASES = {
    "letters": "a" * 100_000,
    "letters-dots": "a." * 50_000,
    "letters-final-dot": "a" * 99_999 + ".",
    "zeros": "0" * 100_000,
    "zeros-spaces": "0 " * 50_000,
    "digits-spaces": "1 " * 50_000 + "x",
    "plus-parentheses": "+(" * 50_000,
    "zero-one-spaces": "0 1 " * 25_000,
    "at-signs": "a@" * 50_000,
    "domain-without-dot": "a@" + "b" * 100_000,
}


@pytest.mark.parametrize("text", WORST_CASES.values(), ids=WORST_CASES.keys())
def test_detection_under_100_ms_on_worst_cases(text: str) -> None:
    start = time.perf_counter()
    contact_reasons(text)
    assert time.perf_counter() - start < 0.1
