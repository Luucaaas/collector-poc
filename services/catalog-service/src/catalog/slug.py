"""URL slug derived from a name: lowercase, accents removed, hyphens (RM-06)."""

import re
import unicodedata


def slugify(name: str) -> str:
    # Ligatures do not decompose under NFKD.
    spelled = name.replace("œ", "oe").replace("Œ", "OE").replace("æ", "ae").replace("Æ", "AE")
    decomposed = unicodedata.normalize("NFKD", spelled)
    ascii_text = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
