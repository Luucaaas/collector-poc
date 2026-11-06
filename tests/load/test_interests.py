"""Test sans réseau du calcul des centres d'intérêt."""

from interests import interests_for_run

CATEGORIES = [
    {"id": "c1", "name": "Figurines"},
    {"id": "c2", "name": "Charge 20261106-1049"},
    {"id": "c3", "name": "Charge 20261106-1051"},
    {"id": "c4", "name": "Chargeur de piles"},  # commence par « Charge » mais sans espace
    {"id": "c5", "name": "Cartes"},
]


def test_previous_runs_removed_others_kept_new_added() -> None:
    result = interests_for_run(["c1", "c2", "c3", "c4", "unknown"], CATEGORIES, "c6")
    assert result == ["c1", "c4", "unknown", "c6"]


def test_run_category_not_duplicated() -> None:
    assert interests_for_run(["c1", "c6"], CATEGORIES, "c6") == ["c1", "c6"]


def test_empty_interests() -> None:
    assert interests_for_run([], CATEGORIES, "c6") == ["c6"]
