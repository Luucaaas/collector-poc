"""Analyse du protocole 5 (charge et disponibilité) : chronologie de l'HPA, p95 et 5xx par phase.

Appelé par `docs/04-experimentations/05-charge-disponibilite/run.sh` une fois le test terminé :
    python phases.py <dossier de résultats> [<adresse de Prometheus>]

Fichiers lus dans le dossier de résultats (tous écrits par `run.sh` ou par le locustfile) :
- `requetes.csv` : une ligne par requête (instant, nom, durée en ms, code HTTP, échec) ;
- `chronologie.tsv` : événements datés par `run.sh` (suppression du pod, remplaçant prêt, arrêt) ;
- `fenetre.json` : début de la phase nominale et du pic, datés par le profil de charge ;
- `hpa.tsv` (instant, HPA, réplicas souhaités, courants, CPU en %), `ready.tsv` (instant,
  déploiement, réplicas prêts) : relevés toutes les 5 s.
Le module est pur : aucune dépendance au réseau hors de la lecture facultative de Prometheus.
"""

import csv
import gzip
import json
import math
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import report
import thresholds
from thresholds import fr

CATALOG = "catalog-service"
LIST_NAME = thresholds.READ_LIST
PUBLISH_NAME = thresholds.PUBLISH


@dataclass(frozen=True)
class Request:
    epoch: float
    name: str
    response_ms: float
    status: int
    failed: bool


@dataclass(frozen=True)
class Sample:
    epoch: float
    name: str
    desired: int
    current: int
    ready: int | None
    cpu_percent: int | None


def percentile(values: list[float], fraction: float) -> float | None:
    """Percentile au rang le plus proche (comme Locust) ; None si la liste est vide."""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def read_requests(path: Path) -> list[Request]:
    """Requêtes de charge seulement : la préparation et la connexion sont exclues."""
    rows: list[Request] = []
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if not thresholds.is_load_request(row["name"]):
                continue
            rows.append(
                Request(
                    float(row["epoch"]),
                    row["name"],
                    float(row["response_ms"]),
                    int(row["status"]),
                    row["failed"] == "1",
                )
            )
    return rows


def read_chronology(path: Path) -> dict[str, float]:
    events: dict[str, float] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            stamp, name, *_ = line.split("\t")
            events[name] = float(stamp)
    return events


def _int_or_none(text: str) -> int | None:
    return int(text) if text.strip().lstrip("-").isdigit() else None


def read_samples(hpa_path: Path, ready_path: Path) -> list[Sample]:
    """Relevés de l'HPA (souhaités, courants, CPU) complétés des réplicas prêts du déploiement.

    Les deux relevés viennent de deux appels à `kubectl` à quelques dixièmes de seconde d'écart :
    chaque ligne de l'HPA prend la valeur la plus proche, à moins de 4 s.
    """
    ready: dict[str, list[tuple[float, int]]] = {}
    for line in ready_path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            ready.setdefault(parts[1], []).append((float(parts[0]), _int_or_none(parts[2]) or 0))
    samples: list[Sample] = []
    for line in hpa_path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) != 5:
            continue
        stamp = float(parts[0])
        near = [(abs(at - stamp), value) for at, value in ready.get(parts[1], [])]
        closest = min(near, default=(math.inf, 0))
        samples.append(
            Sample(
                stamp,
                parts[1],
                _int_or_none(parts[2]) or 0,
                _int_or_none(parts[3]) or 0,
                closest[1] if closest[0] < 4 else None,
                _int_or_none(parts[4]),
            )
        )
    return samples


def first_time(
    samples: list[Sample], name: str, after: float, test: Callable[[Sample], bool]
) -> float | None:
    for sample in samples:
        if sample.name == name and sample.epoch >= after and test(sample):
            return sample.epoch
    return None


@dataclass(frozen=True)
class PhaseStats:
    label: str
    start: float
    end: float
    requests: int
    server_errors: int
    other_failures: int
    p95_list: float | None
    p95_publish: float | None
    p95_all: float | None


def phase_stats(label: str, rows: list[Request], start: float, end: float) -> PhaseStats:
    inside = [r for r in rows if start <= r.epoch < end]
    return PhaseStats(
        label,
        start,
        end,
        len(inside),
        sum(1 for r in inside if r.status >= 500),
        sum(1 for r in inside if r.failed and r.status < 500),
        percentile([r.response_ms for r in inside if r.name == LIST_NAME], 0.95),
        percentile([r.response_ms for r in inside if r.name == PUBLISH_NAME], 0.95),
        percentile([r.response_ms for r in inside], 0.95),
    )


def failures_around(rows: list[Request], moment: float, before: float, after: float) -> list[str]:
    """Échecs dans la fenêtre autour de `moment`, regroupés par seconde, nom et code."""
    counts: dict[tuple[int, str, int], int] = {}
    for r in rows:
        if r.failed and moment - before <= r.epoch < moment + after:
            key = (round(r.epoch - moment), r.name, r.status)
            counts[key] = counts.get(key, 0) + 1
    return [
        f"t{offset:+d} s : {n} × {name} (code {status})"
        for (offset, name, status), n in sorted(counts.items())
    ]


def clock(epoch: float) -> str:
    return time.strftime("%H:%M:%S", time.localtime(epoch))


def _ms(value: float | None) -> str:
    return "n/a" if value is None else f"{fr(value)} ms"


def _rate(errors: int, total: int) -> str:
    return "n/a" if total == 0 else f"{fr(100.0 * errors / total, 2)} %"


def _since(epoch: float | None, origin: float) -> str:
    return "non atteint" if epoch is None else f"{clock(epoch)} (+{fr(epoch - origin)} s)"


@dataclass(frozen=True)
class Timeline:
    nominal_start: float
    peak_start: float
    delete: float | None
    old_gone: float | None
    new_ready: float | None
    recovered: float | None
    stop: float
    reached: dict[int, float | None]  # instant où l'HPA demande n réplicas
    ready_at: dict[int, float | None]  # instant où n réplicas sont prêts
    back_desired: float | None
    back_ready: float | None


def _desired_from(count: int) -> Callable[[Sample], bool]:
    return lambda sample: sample.desired >= count


def _ready_from(count: int) -> Callable[[Sample], bool]:
    return lambda sample: sample.ready is not None and sample.ready >= count


def read_pod_counts(path: Path) -> dict[float, int]:
    """Nombre de pods de `catalog-service` par relevé (pods en cours d'arrêt compris)."""
    counts: dict[float, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[1].startswith(CATALOG):
            counts[float(parts[0])] = counts.get(float(parts[0]), 0) + 1
    return counts


def build_timeline(
    window: dict[str, float],
    events: dict[str, float],
    samples: list[Sample],
    pod_counts: dict[float, int] | None = None,
) -> Timeline:
    """Chronologie. Deux sources : relevés de 5 s (HPA, réplicas prêts de 3 et 4, pods) et
    interrogation toutes les 0,5 s de `run.sh` pour « 5 réplicas prêts » (`five_ready`, plus
    précise, utilisée quand elle existe). Le retour à 2 réplicas est le premier relevé après
    l'arrêt où il ne reste que 2 pods de `catalog-service` (et non le `currentReplicas` de l'HPA,
    en retard sur les pods)."""
    peak = window["peak_start"]
    stop = events["stop"]
    reached = {n: first_time(samples, CATALOG, peak, _desired_from(n)) for n in (3, 4, 5)}
    ready_at = {n: first_time(samples, CATALOG, peak, _ready_from(n)) for n in (3, 4, 5)}
    if "five_ready" in events:
        ready_at[5] = events["five_ready"]
    back_desired = first_time(samples, CATALOG, stop, lambda s: s.desired <= 2)
    if pod_counts is not None:
        back_ready = next(
            (at for at, count in sorted(pod_counts.items()) if at >= stop and count == 2), None
        )
    else:
        back_ready = first_time(
            samples, CATALOG, stop, lambda s: s.current <= 2 and (s.ready or 0) <= 2
        )
    return Timeline(
        window["nominal_start"],
        peak,
        events.get("delete"),
        events.get("old_gone"),
        events.get("new_ready"),
        events.get("recovered"),
        stop,
        reached,
        ready_at,
        back_desired,
        back_ready,
    )


def render(
    timeline: Timeline,
    rows: list[Request],
    samples: list[Sample],
    window: dict[str, float],
    prometheus: tuple[float | None, float | None],
    parameters: str,
) -> str:
    t = timeline
    ramp = max(0.0, window.get("nominal_ramp", 50.0))
    peak_top = t.ready_at[5] if t.ready_at[5] is not None else t.delete or t.stop
    delete = t.delete if t.delete is not None else t.stop
    recovered = t.recovered if t.recovered is not None else t.stop
    phases = [
        phase_stats(
            "Nominale (50 utilisateurs, hors montée)", rows, t.nominal_start + ramp, t.peak_start
        ),
        phase_stats("Pic, montée de l'HPA", rows, t.peak_start, peak_top),
        phase_stats("Pic, 5 réplicas prêts", rows, peak_top, delete),
        phase_stats("Suppression du pod, jusqu'au retour des réplicas", rows, delete, recovered),
        phase_stats("Pic après remplacement", rows, recovered, t.stop),
    ]
    cpu = [s.cpu_percent for s in samples if s.name == CATALOG and s.cpu_percent is not None]
    lines = ["# Résumé de l'exécution de charge et de disponibilité", "", parameters, ""]
    lines += ["## Chronologie (instants locaux, secondes depuis le début du pic)", ""]
    lines += ["| Événement | Instant |", "| --- | --- |"]
    lines += [f"| Début de la charge nominale | {clock(t.nominal_start)} |"]
    lines += [f"| Début du pic | {clock(t.peak_start)} (0 s) |"]
    for n in (3, 4, 5):
        lines += [f"| HPA demande {n} réplicas | {_since(t.reached[n], t.peak_start)} |"]
    for n in (3, 4, 5):
        lines += [f"| {n} réplicas prêts | {_since(t.ready_at[n], t.peak_start)} |"]
    lines += [f"| Suppression d'un pod | {_since(t.delete, t.peak_start)} |"]
    lines += [f"| Ancien pod disparu | {_since(t.old_gone, t.peak_start)} |"]
    lines += [f"| Pod de remplacement prêt | {_since(t.new_ready, t.peak_start)} |"]
    lines += [f"| Tous les réplicas de nouveau prêts | {_since(t.recovered, t.peak_start)} |"]
    lines += [f"| Arrêt de la charge | {_since(t.stop, t.peak_start)} |"]
    lines += [f"| HPA demande 2 réplicas | {_since(t.back_desired, t.peak_start)} |"]
    lines += [f"| Il ne reste que 2 pods | {_since(t.back_ready, t.peak_start)} |"]
    lines += ["", "## Délais", ""]
    if t.delete is not None:
        gone = "n/a" if t.old_gone is None else f"{fr(t.old_gone - t.delete, 1)} s"
        new = "n/a" if t.new_ready is None else f"{fr(t.new_ready - t.delete, 1)} s"
        full = "n/a" if t.recovered is None else f"{fr(t.recovered - t.delete, 1)} s"
        lines += [
            f"- Suppression du pod : ancien pod disparu après {gone}, remplaçant prêt après "
            f"{new}, tous les réplicas de nouveau prêts après {full}."
        ]
    for n in (3, 4, 5):
        asked, ready = t.reached[n], t.ready_at[n]
        if asked is not None:
            done = f", prêts après {fr(ready - t.peak_start)} s." if ready is not None else "."
            lines += [
                f"- Du début du pic à {n} réplicas demandés : {fr(asked - t.peak_start)} s{done}"
            ]
    if t.back_ready is not None:
        lines += [
            f"- De l'arrêt de la charge au retour à 2 réplicas : {fr(t.back_ready - t.stop, 0)} s."
        ]
    else:
        lines += ["- Retour à 2 réplicas : non atteint pendant l'observation."]
    if cpu:
        lines += [
            f"- CPU de `catalog-service` (moyenne des pods, % de leur requête de 100m) : "
            f"maximum relevé {max(cpu)} %."
        ]
    lines += ["", "## Latence et erreurs par phase (requêtes de charge, vues par Locust)", ""]
    lines += [
        "| Phase | Durée | Requêtes | 5xx | Taux de 5xx | Autres échecs | p95 liste "
        "| p95 publication | p95 toutes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for p in phases:
        lines += [
            f"| {p.label} | {fr(p.end - p.start)} s | {p.requests} | {p.server_errors} | "
            f"{_rate(p.server_errors, p.requests)} | {p.other_failures} | {_ms(p.p95_list)} | "
            f"{_ms(p.p95_publish)} | {_ms(p.p95_all)} |"
        ]
    if t.delete is not None:
        lines += ["", "## Échecs autour de la suppression du pod (de -5 s à +60 s)", ""]
        around = failures_around(rows, t.delete, 5, 60)
        lines += [f"- {entry}" for entry in around] or ["- Aucun échec dans la fenêtre."]
    errors, total = prometheus
    lines += ["", "## Côté services (Prometheus, de la charge nominale à l'arrêt)", ""]
    if errors is None or total is None:
        lines += ["- Non mesuré."]
    else:
        lines += [
            f"- {fr(errors)} réponses 5xx sur {fr(total)} requêtes "
            f"({_rate(int(errors), int(total))})."
        ]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3):
        print("usage : phases.py <dossier de résultats> [<adresse de Prometheus>]", file=sys.stderr)
        return 2
    directory = Path(argv[1])
    window = {
        k: float(v)
        for k, v in json.loads((directory / "fenetre.json").read_text()).items()
        if isinstance(v, int | float)
    }
    events = read_chronology(directory / "chronologie.tsv")
    samples = read_samples(directory / "hpa.tsv", directory / "ready.tsv")
    requests = directory / "requetes.csv"
    rows = read_requests(requests if requests.exists() else directory / "requetes.csv.gz")
    pods = read_pod_counts(directory / "pods.tsv")
    timeline = build_timeline(window, events, samples, pods)
    prom: tuple[float | None, float | None] = (None, None)
    if len(argv) == 3:
        base = argv[2].rstrip("/")
        at = events["stop"] + 30
        span = f"{math.ceil(at - timeline.nominal_start)}s"
        selector = 'job=~"catalog-service|notification-service",handler!~"/health.*|/metrics"'
        errors = report.instant_value(
            report.http_fetch,
            base,
            f'sum(increase(http_requests_total{{{selector},status="5xx"}}[{span}])) or vector(0)',
            at,
        )
        total = report.instant_value(
            report.http_fetch, base, f"sum(increase(http_requests_total{{{selector}}}[{span}]))", at
        )
        prom = (errors, total)
        (directory / "prometheus.json").write_text(
            json.dumps({"errors": errors, "total": total}), encoding="utf-8"
        )
    elif (directory / "prometheus.json").exists():
        # Régénération sans Prometheus (rétention de 2 h dépassée) : valeurs de la première analyse.
        saved = json.loads((directory / "prometheus.json").read_text(encoding="utf-8"))
        prom = (saved["errors"], saved["total"])
    parameters = (directory / "parametres.txt").read_text(encoding="utf-8").strip()
    text = render(timeline, rows, samples, window, prom, parameters)
    (directory / "resume.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
