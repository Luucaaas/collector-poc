"""Générateur de charge : un nombre connu de requêtes, dans des proportions connues.

Cycle de 20 requêtes : 17 GET /items, 2 GET /slow, 1 GET /fail (85 %, 10 %, 5 %), envoyées à
cadence fixe (--rate par seconde, une requête lancée toutes les 1/rate s, sans attendre la
réponse de la précédente). Écrit une ligne `RESULT {...}` : horodatages de début et de fin
(horloge du cluster), compteurs réellement envoyés et latences mesurées côté client.
"""

import argparse
import asyncio
import json
import math
import time
from collections import defaultdict

import httpx


def path_for(index: int) -> str:
    """Répartit les chemins dans le cycle, en intercalant les lents et l'échec."""
    slot = index % 20
    if slot in (0, 10):
        return "/slow"
    if slot == 5:
        return "/fail"
    return "/items"


def percentile(values: list[float], q: float) -> float:
    """Percentile par rang (méthode du plus proche rang)."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)]


async def main(url: str, total: int, rate: float) -> None:
    latencies: dict[str, list[float]] = defaultdict(list)
    statuses: dict[str, int] = defaultdict(int)

    async def one(client: httpx.AsyncClient, path: str) -> None:
        started = time.perf_counter()
        response = await client.get(url + path)
        latencies[path].append(time.perf_counter() - started)
        statuses[f"{path} {response.status_code}"] += 1

    limits = httpx.Limits(max_connections=100)
    async with httpx.AsyncClient(limits=limits, timeout=30) as client:
        start_ts = time.time()
        origin = time.perf_counter()
        tasks = []
        for i in range(total):
            delay = origin + i / rate - time.perf_counter()
            if delay > 0:
                await asyncio.sleep(delay)
            tasks.append(asyncio.create_task(one(client, path_for(i))))
        await asyncio.gather(*tasks)
        end_ts = time.time()

    everything = [v for values in latencies.values() for v in values]
    result = {
        "start_ts": round(start_ts, 3),
        "end_ts": round(end_ts, 3),
        "total": total,
        "rate": rate,
        "statuses": dict(sorted(statuses.items())),
        "client_p95_s": {
            **{p: round(percentile(v, 0.95), 4) for p, v in sorted(latencies.items())},
            "all": round(percentile(everything, 0.95), 4),
        },
    }
    print("RESULT " + json.dumps(result), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--total", type=int, required=True)
    parser.add_argument("--rate", type=float, required=True)
    args = parser.parse_args()
    asyncio.run(main(args.url, args.total, args.rate))
