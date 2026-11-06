"""Calcul de la liste des centres d'intérêt de chloe pour une exécution (module pur)."""

from typing import Any

# Préfixe des catégories créées par les exécutions de charge (`Charge <date>`).
RUN_CATEGORY_PREFIX = "Charge "


def interests_for_run(
    current_ids: list[str], categories: list[dict[str, Any]], run_category_id: str
) -> list[str]:
    """Nouvelle liste : sans les catégories des exécutions précédentes, avec celle de celle-ci.

    La limite métier est de 20 centres d'intérêt : sans ce retrait, chloe l'atteindrait après une
    vingtaine d'exécutions. Seules les catégories dont le nom commence par « Charge » sont
    retirées ; toutes les autres (y compris un identifiant que le catalogue ne connaît plus) sont
    gardées, dans leur ordre.
    """
    previous_runs = {
        str(category["id"])
        for category in categories
        if str(category["name"]).startswith(RUN_CATEGORY_PREFIX)
    }
    kept = [identifier for identifier in current_ids if identifier not in previous_runs]
    if run_category_id not in kept:
        kept.append(run_category_id)
    return kept
