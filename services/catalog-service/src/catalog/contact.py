"""Contact details detection (RM-02): pure module, no I/O, reused by the articles (P4-03).

Obfuscated forms (« zéro six… », « arobase », « jean @ example.com ») and the text of images
are out of the POC.

Method for phone numbers: dates (dd.mm.yyyy) are removed first, then we look for runs
of digits and separators (spaces, including non-breaking and thin ones, dot, hyphen, slash,
parentheses), even stuck to letters (« tel0612345678 »). A run is a number if it is:
- national: 10 consecutive digits, taken at a group boundary, starting with 0 then a
  digit from 1 to 9, whatever the splitting and the separators (« 06 1234 5678 »,
  « 06.12 34-56 78 », « 0 6 1 2 3 4 5 6 7 8 »);
- international: prefix `+` or `00`, then 9 to 15 digits (« +12 000 000 copies » and
  « Series 00 1234 5678 » are not).
Limit: a number stuck to other digits without a separator (« 106 12 34 56 78 ») is not read.
"""

import re
from itertools import accumulate

CONTACT_EMAIL = "CONTACT_EMAIL"
CONTACT_PHONE = "CONTACT_PHONE"

# The pattern starts at the « @ »: the local part only needs one valid character before it (a
# single-character lookbehind). A local part repeated at the start of the pattern restarted, at each
# position of a long run without « @ », a scan to the end (quadratic cost, Sonar rule
# python:S8786). Detection is the same: an address exists if and only if an « @ » is
# preceded by a character of the local part and followed by a domain with at least one dot.
_EMAIL = re.compile(r"(?<=[\w.+-])@[\w-]+(?:\.[\w-]+)+")

# Date dd.mm.yyyy (constant separator): followed by a time (« 05.11.2024 14h »), it would give
# 10 digits starting with 0.
_DATE = re.compile(r"(?<!\d)\d{1,2}([./-])\d{1,2}\1(?:19|20)\d{2}(?!\d)")
# Second digit different from 0, any Unicode digit included (like `\d` in _CANDIDATE): a
# number written in Arabic-Indic digits (« 0٦12345678 ») is still detected.
_NATIONAL_START = re.compile(r"0(?=(?!0)\d)")
_CANDIDATE = re.compile(r"\+?\(?\d[\d\s.\-/()]*\d")


def _is_national(groups: list[str]) -> bool:
    # Linear equivalent of « from each group, accumulate groups up to at least
    # 10 digits, and test whether we have exactly 10 starting with 0 then 1 to 9 »: a number
    # starts at a group boundary where we find « 0 » then 1 to 9, and ends at a boundary.
    digits = "".join(groups)
    ends = set(accumulate(map(len, groups)))
    boundaries = ends | {0}
    return any(
        match.start() in boundaries and match.start() + 10 in ends
        for match in _NATIONAL_START.finditer(digits)
    )


def _is_phone(candidate: str) -> bool:
    groups = re.findall(r"\d+", candidate)
    digits = "".join(groups)
    if candidate.startswith("+"):
        return 9 <= len(digits) <= 15
    if digits.startswith("00") and 9 <= len(digits) - 2 <= 15:
        return True
    return _is_national(groups)


def _has_email(text: str) -> bool:
    return _EMAIL.search(text) is not None


def _has_phone(text: str) -> bool:
    text = _DATE.sub(" ", text)
    return any(_is_phone(match.group()) for match in _CANDIDATE.finditer(text))


def contact_reasons(*texts: str | None) -> list[str]:
    """Reasons found in the texts: `CONTACT_EMAIL` then `CONTACT_PHONE`, without duplicates."""
    present = [text for text in texts if text]
    reasons: list[str] = []
    if any(_has_email(text) for text in present):
        reasons.append(CONTACT_EMAIL)
    if any(_has_phone(text) for text in present):
        reasons.append(CONTACT_PHONE)
    return reasons
