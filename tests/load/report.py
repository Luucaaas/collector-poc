"""Writes `resume.md` from the Locust CSV files and the Prometheus measurements.

Called by `run.sh` once Locust has finished:
    python report.py <results directory> <Prometheus address>

Prometheus is queried over the plateau window (from `spawning_complete` to `test_stop`, recorded
by the locustfile in `fenetre.json`), evaluated a little after the end to let the last scrape
pass: the `ServiceMonitor` scrapes every 15 s, so 35 s leave two complete cycles.
"""

import json
import math
import sys
import time
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path

import thresholds

# Delay left to Prometheus to scrape the last samples after the end of the test.
SETTLE_SECONDS = 35

Fetch = Callable[[str], dict[str, object]]


def http_fetch(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=10) as reply:
        data: dict[str, object] = json.load(reply)
    return data


def instant_value(fetch: Fetch, base: str, expr: str, at: float) -> float | None:
    """Value of a Prometheus instant query; None on error, empty series or NaN."""
    query = urllib.parse.urlencode({"query": expr, "time": f"{at:.3f}"})
    try:
        payload = fetch(f"{base}/api/v1/query?{query}")
        result = payload["data"]["result"]  # type: ignore[index]
        if not result:
            return None
        value = float(result[0]["value"][1])
    except (OSError, KeyError, IndexError, TypeError, ValueError):
        return None
    return None if math.isnan(value) else value


def prometheus_measures(
    fetch: Fetch, base: str, start: float, end: float
) -> tuple[float | None, float | None, float | None]:
    """(5xx on the services side, total requests on the services side, notification delay p95)."""
    at = end + SETTLE_SECONDS
    window = f"{max(1, math.ceil(at - start))}s"
    selector = 'job=~"catalog-service|notification-service",handler!~"/health.*|/metrics"'
    errors = instant_value(
        fetch,
        base,
        f'sum(increase(http_requests_total{{{selector},status="5xx"}}[{window}])) or vector(0)',
        at,
    )
    total = instant_value(
        fetch, base, f"sum(increase(http_requests_total{{{selector}}}[{window}]))", at
    )
    delay = instant_value(
        fetch,
        base,
        "histogram_quantile(0.95, sum by (le) "
        f"(increase(notification_delay_seconds_bucket[{window}])))",
        at,
    )
    return errors, total, delay


def build_resume(directory: Path, prometheus: str, fetch: Fetch = http_fetch) -> str:
    stats = thresholds.read_stats(directory / "locust_stats.csv")
    server_errors, _other = thresholds.count_5xx(directory / "locust_failures.csv")
    window = json.loads((directory / "fenetre.json").read_text())
    start, end = float(window["plateau_start"]), float(window["end"])
    errors, total, delay = prometheus_measures(fetch, prometheus, start, end)
    checks = thresholds.build_checks(stats, server_errors, errors, total, delay)
    environment = "\n\n".join(
        part.read_text()
        for part in (
            directory / "environnement.txt",
            directory / "hpa-avant.txt",
            directory / "hpa-apres.txt",
        )
        if part.exists()
    )
    fmt = "%d/%m/%Y %H:%M:%S"
    description = (
        f"Plateau de {time.strftime(fmt, time.localtime(start))} à "
        f"{time.strftime(fmt, time.localtime(end))} ({end - start:.0f} s), catégorie de "
        f"l'exécution « {window.get('category', '?')} ». Prometheus interrogé {SETTLE_SECONDS} s "
        "après la fin pour inclure la dernière collecte."
    )
    others = thresholds.count_5xx(directory / "locust_failures.csv")[1]
    if others:
        description += f" Autres échecs (4xx inattendus, erreurs de connexion) : {others}."
    return thresholds.render_resume(
        "Résumé de l'exécution de charge",
        checks,
        thresholds.informative_rows(stats),
        stats,
        environment,
        description,
    )


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: report.py <results directory> <Prometheus address>", file=sys.stderr)
        return 2
    directory = Path(argv[1])
    resume = build_resume(directory, argv[2].rstrip("/"))
    (directory / "resume.md").write_text(resume, encoding="utf-8")
    print(resume)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
