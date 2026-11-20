"""Computation of chloe's interest list for a run (pure module)."""

from typing import Any

# Prefix of the categories created by load runs (`Charge <date>`).
RUN_CATEGORY_PREFIX = "Charge "


def interests_for_run(
    current_ids: list[str], categories: list[dict[str, Any]], run_category_id: str
) -> list[str]:
    """New list: without the categories of previous runs, with the one of this run.

    The business limit is 20 interests: without this removal, chloe would reach it after about
    twenty runs. Only the categories whose name starts with « Charge » are removed; all the
    others (including an identifier the catalogue no longer knows) are kept,
    in their order.
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
