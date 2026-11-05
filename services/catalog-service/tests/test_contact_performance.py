"""Régression de Sonar python:S8786 : la détection des coordonnées est en temps linéaire."""

import time

import pytest

from catalog.contact import contact_reasons

# Textes de pire cas : longues suites sans « @ », chiffres et séparateurs alternés.
WORST_CASES = {
    "lettres": "a" * 100_000,
    "lettres-points": "a." * 50_000,
    "lettres-point-final": "a" * 99_999 + ".",
    "zeros": "0" * 100_000,
    "zeros-espaces": "0 " * 50_000,
    "chiffres-espaces": "1 " * 50_000 + "x",
    "plus-parentheses": "+(" * 50_000,
    "zero-un-espaces": "0 1 " * 25_000,
    "arobases": "a@" * 50_000,
    "domaine-sans-point": "a@" + "b" * 100_000,
}


@pytest.mark.parametrize("text", WORST_CASES.values(), ids=WORST_CASES.keys())
def test_detection_en_moins_de_100_ms_sur_les_pires_cas(text: str) -> None:
    start = time.perf_counter()
    contact_reasons(text)
    assert time.perf_counter() - start < 0.1
