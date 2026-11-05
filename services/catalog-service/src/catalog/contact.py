"""Détection des coordonnées (RM-02) : module pur, sans I/O, réutilisé par les articles (P4-03).

Les formes obfusquées (« zéro six… », « arobase », « jean @ example.com ») et le texte des images
sont hors du POC.

Méthode pour les téléphones : on retire d'abord les dates (jj.mm.aaaa), puis on cherche des suites
de chiffres et de séparateurs (espaces, y compris insécables et fines, point, tiret, barre oblique,
parenthèses), même collées à des lettres (« tel0612345678 »). Une suite est un numéro :
- national : 10 chiffres consécutifs, pris à une frontière de groupe, commençant par 0 puis un
  chiffre de 1 à 9, quels que soient le découpage et les séparateurs (« 06 1234 5678 »,
  « 06.12 34-56 78 », « 0 6 1 2 3 4 5 6 7 8 ») ;
- international : préfixe `+` ou `00`, puis 9 à 15 chiffres (« +12 000 000 exemplaires » et
  « Série 00 1234 5678 » n'en sont pas).
Limite : un numéro collé à d'autres chiffres sans séparateur (« 106 12 34 56 78 ») n'est pas lu.
"""

import re
from itertools import accumulate

CONTACT_EMAIL = "CONTACT_EMAIL"
CONTACT_PHONE = "CONTACT_PHONE"

# Le motif part de l'« @ » : la partie locale n'a besoin que d'un caractère valide avant lui (un
# lookbehind d'un seul caractère). Une partie locale répétée au début du motif relançait, à chaque
# position d'une longue suite sans « @ », un balayage jusqu'à la fin (coût quadratique, règle Sonar
# python:S8786). La détection est la même : une adresse existe si et seulement si un « @ » est
# précédé d'un caractère de la partie locale et suivi d'un domaine à au moins un point.
_EMAIL = re.compile(r"(?<=[\w.+-])@[\w-]+(?:\.[\w-]+)+")

# Date jj.mm.aaaa (séparateur constant) : suivie d'une heure (« 05.11.2024 14h »), elle donnerait
# 10 chiffres commençant par 0.
_DATE = re.compile(r"(?<!\d)\d{1,2}([./-])\d{1,2}\1(?:19|20)\d{2}(?!\d)")
_NATIONAL_START = re.compile(r"0(?=[1-9])")
_CANDIDATE = re.compile(r"\+?\(?\d[\d\s.\-/()]*\d")


def _is_national(groups: list[str]) -> bool:
    # Équivalent linéaire de « à partir de chaque groupe, accumuler des groupes jusqu'à au moins
    # 10 chiffres, et tester si on en a exactement 10 commençant par 0 puis 1 à 9 » : un numéro
    # commence à une frontière de groupe où l'on trouve « 0 » puis 1 à 9, et finit à une frontière.
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
    """Motifs trouvés dans les textes : `CONTACT_EMAIL` puis `CONTACT_PHONE`, sans doublon."""
    present = [text for text in texts if text]
    reasons: list[str] = []
    if any(_has_email(text) for text in present):
        reasons.append(CONTACT_EMAIL)
    if any(_has_phone(text) for text in present):
        reasons.append(CONTACT_PHONE)
    return reasons
