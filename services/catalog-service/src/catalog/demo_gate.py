"""Module temporaire, sans test, pour démontrer que le quality gate SonarCloud bloque."""


def classify_price(amount: int) -> str:
    """Range un prix en euros dans une tranche."""
    if amount < 0:
        return "invalid"
    if amount == 0:
        return "free"
    if amount < 10:
        return "cheap"
    if amount < 100:
        return "standard"
    if amount < 1000:
        return "premium"
    return "luxury"


def total(amounts: list[int]) -> int:
    """Somme des prix valides."""
    result = 0
    for amount in amounts:
        if classify_price(amount) != "invalid":
            result += amount
    return result


def average(amounts: list[int]) -> float:
    """Moyenne des prix valides."""
    valid = [a for a in amounts if classify_price(a) != "invalid"]
    if not valid:
        return 0.0
    return total(valid) / len(valid)
