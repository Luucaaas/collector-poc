"""Seuils de l'indicateur I3 et de l'exigence ENF-14, comparaison aux mesures et `resume.md`.

Module pur : il reçoit des nombres et renvoie du texte, sans réseau ni fichier (sauf `read_*`).
"""

import csv
import math
from dataclasses import dataclass
from pathlib import Path

# Noms des requêtes dans Locust (regroupés : pas un nom par identifiant d'article).
READ_LIST = "GET /articles"
READ_OTHERS = ("GET /categories", "GET /articles/{id}")
PUBLISH = "POST /articles"
PREPARATION_PREFIXES = ("[prépa]", "[connexion]")

READ_P95_MS = 300.0  # ENF-12, I3
PUBLISH_P95_MS = 500.0  # ENF-12, I3
ERROR_RATE_PERCENT = 1.0  # ENF-13, I3
NOTIFICATION_P95_SECONDS = 2.0  # ENF-14
FIRST_BUCKET_SECONDS = 0.1  # première borne de notification_delay_seconds


@dataclass(frozen=True)
class RequestStats:
    name: str
    requests: int
    failures: int
    p95_ms: float
    median_ms: float


@dataclass(frozen=True)
class Check:
    label: str
    value: str  # valeur mesurée, déjà formatée ("212 ms") ou "non mesuré"
    threshold: str
    verdict: str  # "conforme", "non conforme" ou "non mesuré"
    note: str = ""


def fr(value: float, decimals: int = 0) -> str:
    """Nombre au format français (virgule décimale)."""
    return f"{value:.{decimals}f}".replace(".", ",")


def is_load_request(name: str) -> bool:
    """Vrai pour une requête de charge ; faux pour la préparation et la connexion (hors seuils)."""
    return not name.startswith(PREPARATION_PREFIXES)


def _milliseconds(value: str) -> float:
    """Locust écrit « N/A » pour une requête qui n'a eu aucune réponse (échec de connexion)."""
    try:
        return float(value)
    except ValueError:
        return math.nan


def read_stats(path: Path) -> dict[str, RequestStats]:
    """Lit `<préfixe>_stats.csv` de Locust (une ligne par nom de requête, plus « Aggregated »)."""
    stats: dict[str, RequestStats] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            stats[row["Name"]] = RequestStats(
                name=row["Name"],
                requests=int(row["Request Count"]),
                failures=int(row["Failure Count"]),
                p95_ms=_milliseconds(row["95%"]),
                median_ms=_milliseconds(row["50%"]),
            )
    return stats


def count_5xx(path: Path) -> tuple[int, int]:
    """Lit `<préfixe>_failures.csv` : (échecs 5xx, autres échecs) hors préparation et connexion.

    Les scénarios écrivent « HTTP 5xx : <code> » pour une réponse 5xx et une autre formule pour les
    autres échecs (4xx inattendu, erreur de connexion).
    """
    server = other = 0
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if not is_load_request(row["Name"]):
                continue
            occurrences = int(row["Occurrences"])
            if "HTTP 5xx" in row["Error"]:
                server += occurrences
            else:
                other += occurrences
    return server, other


def total_requests(stats: dict[str, RequestStats]) -> int:
    return sum(
        s.requests for name, s in stats.items() if is_load_request(name) and name != "Aggregated"
    )


def _latency_check(
    label: str, stats: dict[str, RequestStats], name: str, limit_ms: float, note: str = ""
) -> Check:
    found = stats.get(name)
    threshold = f"p95 < {fr(limit_ms)} ms"
    if found is None or found.requests == 0:
        return Check(label, "non mesuré", threshold, "non mesuré", "aucune requête")
    if math.isnan(found.p95_ms):
        note = "toutes les requêtes ont échoué"
        return Check(label, "aucune réponse", threshold, "non conforme", note)
    verdict = "conforme" if found.p95_ms < limit_ms else "non conforme"
    return Check(
        label, f"{fr(found.p95_ms)} ms", threshold, verdict, note or f"{found.requests} requêtes"
    )


def _rate_check(label: str, errors: int | None, total: int | None, note: str = "") -> Check:
    threshold = f"< {fr(ERROR_RATE_PERCENT)} %"
    if errors is None or not total:
        return Check(label, "non mesuré", threshold, "non mesuré", note)
    rate = 100.0 * errors / total
    verdict = "conforme" if rate < ERROR_RATE_PERCENT else "non conforme"
    return Check(label, f"{fr(rate, 3)} % ({errors} sur {total})", threshold, verdict, note)


def build_checks(
    stats: dict[str, RequestStats],
    server_errors: int,
    services_5xx: float | None,
    services_total: float | None,
    notification_p95_s: float | None,
) -> list[Check]:
    """Les mesures comparées à leurs seuils, dans l'ordre du résumé."""
    checks = [
        _latency_check("Lecture du catalogue (liste)", stats, READ_LIST, READ_P95_MS),
        _latency_check("Publication d'article", stats, PUBLISH, PUBLISH_P95_MS),
        _rate_check(
            "Réponses 5xx, vues par Locust",
            server_errors,
            total_requests(stats),
            "toutes requêtes de charge",
        ),
        _rate_check(
            "Réponses 5xx, vues par les services",
            None if services_5xx is None else round(services_5xx),
            None if services_total is None else round(services_total),
            "Prometheus, hors sondes et /metrics",
        ),
    ]
    threshold = f"p95 < {fr(NOTIFICATION_P95_SECONDS)} s"
    if notification_p95_s is None:
        checks.append(
            Check(
                "Délai des notifications (ENF-14)",
                "non mesuré",
                threshold,
                "non mesuré",
                "Prometheus sans donnée",
            )
        )
    else:
        verdict = "conforme" if notification_p95_s < NOTIFICATION_P95_SECONDS else "non conforme"
        if notification_p95_s <= FIRST_BUCKET_SECONDS:
            # Le p95 tombe dans le premier seau de l'histogramme : Prometheus interpole dans
            # l'intervalle, la valeur exacte n'est pas connue, seulement qu'elle est sous 0,1 s.
            value = f"moins de {fr(FIRST_BUCKET_SECONDS, 1)} s"
            note = (
                f"Prometheus ; p95 interpolé dans le seau 0 à {fr(FIRST_BUCKET_SECONDS, 1)} s "
                f"(valeur interpolée : {fr(notification_p95_s, 3)} s)"
            )
        else:
            value = f"{fr(notification_p95_s, 3)} s"
            note = "Prometheus, toutes les notifications de la fenêtre"
        checks.append(Check("Délai des notifications (ENF-14)", value, threshold, verdict, note))
    return checks


def informative_rows(stats: dict[str, RequestStats]) -> list[Check]:
    """Autres lectures et changements de prix, comparés au seuil de lecture ou de publication."""
    rows = [
        _latency_check(f"{name} (complément)", stats, name, READ_P95_MS) for name in READ_OTHERS
    ]
    rows.append(
        _latency_check(
            "PUT /articles/{id}/price (complément)",
            stats,
            "PUT /articles/{id}/price",
            PUBLISH_P95_MS,
        )
    )
    return rows


def render_resume(
    title: str,
    checks: list[Check],
    extra_rows: list[Check],
    stats: dict[str, RequestStats],
    environment: str,
    window: str,
) -> str:
    """Rédige `resume.md` : mesures et verdicts, détail par requête, environnement."""
    failed = [c.label for c in checks if c.verdict == "non conforme"]
    unknown = [c.label for c in checks if c.verdict == "non mesuré"]
    if failed:
        overall = "**Hors seuil** : " + ", ".join(failed) + "."
    elif unknown:
        overall = "Aucun dépassement, mais des mesures manquantes : " + ", ".join(unknown) + "."
    else:
        overall = "**Tous les seuils sont respectés.**"
    lines = [
        f"# {title}",
        "",
        overall,
        "",
        "Code de sortie de `run.sh` : 0 dans tous les cas (un dépassement ouvre un ticket de dette "
        "sans bloquer, conformément au processus de test).",
        "",
        "## Mesures et seuils",
        "",
        "| Mesure | Valeur | Seuil | Verdict | Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines += [_row(c) for c in checks]
    lines += [
        "",
        "Le total vu par les services (Prometheus) diffère de celui de Locust : `increase()` est "
        "calculé sur une fenêtre élargie de 35 s après la fin du test (dernière collecte) et "
        "extrapolé aux bords de la fenêtre, et il compte aussi les requêtes qui ne viennent pas "
        "de Locust.",
        "",
        "Compléments (mêmes seuils de lecture ou de publication, à titre indicatif) :",
        "",
    ]
    lines += ["| Mesure | Valeur | Seuil | Verdict | Source |", "| --- | --- | --- | --- | --- |"]
    lines += [_row(c) for c in extra_rows]
    lines += ["", "## Détail par requête (Locust, plateau seulement)", ""]
    lines += [
        "| Requête | Requêtes | Échecs | Médiane (ms) | p95 (ms) |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    # Les lignes sans requête (préparation et connexion, remises à zéro au plateau) sont omises.
    for name in sorted(n for n in stats if n != "Aggregated" and stats[n].requests > 0):
        s = stats[name]
        marker = " (hors seuils)" if not is_load_request(name) else ""
        lines.append(
            f"| {name}{marker} | {s.requests} | {s.failures} | {fr(s.median_ms)} | {fr(s.p95_ms)} |"
        )
    lines += [
        "",
        "## Fenêtre de mesure",
        "",
        window,
        "",
        "## Environnement",
        "",
        "```",
        environment.rstrip(),
        "```",
        "",
    ]
    return "\n".join(lines)


def _row(check: Check) -> str:
    return f"| {check.label} | {check.value} | {check.threshold} | {check.verdict} | {check.note} |"
