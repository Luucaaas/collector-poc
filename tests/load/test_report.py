"""Tests des seuils, de la lecture des CSV de Locust et de la rédaction de `resume.md`."""

import json
from pathlib import Path

import report
import thresholds as t

STATS_HEADER = "Type,Name,Request Count,Failure Count,50%,95%\n"


def make_stats(read: float = 120, publish: float = 300) -> dict[str, t.RequestStats]:
    def row(name: str, count: int, p95: float) -> t.RequestStats:
        return t.RequestStats(name, count, 0, p95, p95 / 2)

    return {
        t.READ_LIST: row(t.READ_LIST, 4000, read),
        "GET /categories": row("GET /categories", 1500, 80),
        "GET /articles/{id}": row("GET /articles/{id}", 2000, 90),
        t.PUBLISH: row(t.PUBLISH, 500, publish),
        "PUT /articles/{id}/price": row("PUT /articles/{id}/price", 300, 200),
        "[connexion] formulaire": row("[connexion] formulaire", 12, 900),
        "[prépa] vide": row("[prépa] vide", 0, 0),
        "Aggregated": row("Aggregated", 8312, 300),
    }


def verdicts(checks: list[t.Check]) -> dict[str, str]:
    return {c.label: c.verdict for c in checks}


def test_all_conform() -> None:
    checks = t.build_checks(make_stats(), 0, 0.0, 5000.0, 0.45)
    assert set(verdicts(checks).values()) == {"conforme"}


def test_read_threshold_is_strict() -> None:
    assert (
        verdicts(t.build_checks(make_stats(read=299), 0, 0, 100, 1))["Lecture du catalogue (liste)"]
        == "conforme"
    )
    assert (
        verdicts(t.build_checks(make_stats(read=300), 0, 0, 100, 1))["Lecture du catalogue (liste)"]
        == "non conforme"
    )


def test_publish_over_threshold() -> None:
    checks = t.build_checks(make_stats(publish=650), 0, 0, 100, 1)
    assert verdicts(checks)["Publication d'article"] == "non conforme"


def test_error_rate_ignores_login_and_aggregated() -> None:
    # 4000 + 1500 + 2000 + 500 + 300 requêtes de charge ; la connexion et le total sont exclus.
    assert t.total_requests(make_stats()) == 8300
    checks = t.build_checks(make_stats(), 83, 0, 100, 1)  # 1,0 % exactement : non conforme
    assert verdicts(checks)["Réponses 5xx, vues par Locust"] == "non conforme"
    checks = t.build_checks(make_stats(), 82, 0, 100, 1)
    assert verdicts(checks)["Réponses 5xx, vues par Locust"] == "conforme"


def test_missing_prometheus_is_not_measured() -> None:
    checks = t.build_checks(make_stats(), 0, None, None, None)
    values = verdicts(checks)
    assert values["Réponses 5xx, vues par les services"] == "non mesuré"
    assert values["Délai des notifications (ENF-14)"] == "non mesuré"


def test_notification_delay_threshold() -> None:
    checks = t.build_checks(make_stats(), 0, 0, 100, 2.0)
    assert verdicts(checks)["Délai des notifications (ENF-14)"] == "non conforme"


def test_render_resume_states_overall_result() -> None:
    stats = make_stats(read=450)
    checks = t.build_checks(stats, 0, 0, 100, 0.4)
    text = t.render_resume("Titre", checks, t.informative_rows(stats), stats, "env", "fenêtre")
    assert "**Hors seuil** : Lecture du catalogue (liste)." in text
    assert "| Lecture du catalogue (liste) | 450 ms | p95 < 300 ms | non conforme |" in text
    assert "[connexion] formulaire (hors seuils)" in text
    assert "[prépa] vide" not in text  # une ligne sans requête n'est pas listée
    assert "| Aggregated" not in text


def test_render_resume_all_conform() -> None:
    stats = make_stats()
    checks = t.build_checks(stats, 0, 0, 100, 0.4)
    text = t.render_resume("Titre", checks, t.informative_rows(stats), stats, "env", "fenêtre")
    assert "**Tous les seuils sont respectés.**" in text


def write_run(directory: Path) -> None:
    (directory / "locust_stats.csv").write_text(
        STATS_HEADER
        + "GET,GET /articles,100,0,40,120\n"
        + "POST,POST /articles,50,2,80,310\n"
        + ",Aggregated,150,2,50,200\n"
    )
    (directory / "locust_failures.csv").write_text(
        "Method,Name,Error,Occurrences\n"
        "POST,POST /articles,HTTP 5xx : 503,2\n"
        "POST,[connexion] formulaire,HTTP 5xx : 502,4\n"
        "GET,GET /articles,HTTP 404 inattendu,3\n"
    )
    (directory / "fenetre.json").write_text(
        json.dumps({"plateau_start": 1000.0, "end": 1310.0, "category": "Charge test"})
    )
    (directory / "environnement.txt").write_text("tag sha-abc1234\n")


def test_read_stats_and_failures(tmp_path: Path) -> None:
    write_run(tmp_path)
    stats = t.read_stats(tmp_path / "locust_stats.csv")
    assert stats["POST /articles"].p95_ms == 310
    assert t.count_5xx(tmp_path / "locust_failures.csv") == (2, 3)  # la connexion est exclue


def test_build_resume_queries_prometheus_on_plateau_window(tmp_path: Path) -> None:
    write_run(tmp_path)
    urls: list[str] = []

    def fetch(url: str) -> dict[str, object]:
        urls.append(url)
        value = "0.8" if "histogram_quantile" in url else "50" if "5xx" in url else "1000"
        return {"data": {"result": [{"value": [1345, value]}]}}

    text = report.build_resume(tmp_path, "http://prom", fetch)
    assert len(urls) == 3
    # Fenêtre : de 1000 à 1310 + 35 s de délai = 345 s.
    assert all("345s" in __import__("urllib.parse").parse.unquote(u) for u in urls)
    assert "| Délai des notifications (ENF-14) | 0,800 s | p95 < 2 s | conforme |" in text
    assert "| Réponses 5xx, vues par les services | 5,000 % (50 sur 1000)" in text
    assert "tag sha-abc1234" in text
    assert "Charge test" in text


def test_prometheus_errors_give_no_value() -> None:
    def broken(url: str) -> dict[str, object]:
        raise OSError("hors ligne")

    assert report.instant_value(broken, "http://prom", "up", 1.0) is None
    empty = report.instant_value(lambda u: {"data": {"result": []}}, "http://prom", "up", 1.0)
    assert empty is None
    nan = report.instant_value(
        lambda u: {"data": {"result": [{"value": [1, "NaN"]}]}}, "http://prom", "up", 1.0
    )
    assert nan is None


def test_read_stats_accepts_not_available_percentiles(tmp_path: Path) -> None:
    (tmp_path / "locust_stats.csv").write_text(STATS_HEADER + "GET,GET /articles,10,10,N/A,N/A\n")
    stats = t.read_stats(tmp_path / "locust_stats.csv")
    assert stats["GET /articles"].failures == 10
    # Pas de latence mesurable : la comparaison ne doit pas déclarer « conforme ».
    check = t.build_checks(stats, 0, 0, 100, 1)[0]
    assert check.verdict == "non conforme"


def test_french_number_format() -> None:
    assert t.fr(2.5, 1) == "2,5"
    assert t.fr(300) == "300"


def test_first_bucket_delay_is_flagged_as_interpolated() -> None:
    check = t.build_checks(make_stats(), 0, 0, 100, 0.095)[-1]
    assert check.value == "moins de 0,1 s"
    assert "interpolé dans le seau 0 à 0,1 s" in check.note
    assert check.verdict == "conforme"
