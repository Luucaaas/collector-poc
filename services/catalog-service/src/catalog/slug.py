"""Slug d'URL dérivé d'un nom : minuscules, accents retirés, tirets (RM-06)."""

import re
import unicodedata


def slugify(name: str) -> str:
    # Les ligatures ne se décomposent pas en NFKD.
    spelled = name.replace("œ", "oe").replace("Œ", "OE").replace("æ", "ae").replace("Æ", "AE")
    decomposed = unicodedata.normalize("NFKD", spelled)
    ascii_text = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
