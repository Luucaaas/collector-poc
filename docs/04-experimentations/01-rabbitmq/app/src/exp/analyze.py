"""Analyse : vide exp.receipts et calcule les mesures d'un scénario (JSON sur la sortie)."""

import argparse
import asyncio
import json
import time
from typing import Any

from exp.common import RECEIPTS_QUEUE, connect

IDLE_SECONDS = 8.0


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--expected", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--delete-ts", type=float, default=0.0)
    parser.add_argument("--poison-id", default="")
    args = parser.parse_args()

    expected_ids = {f"{args.run_id}-{i:05d}" for i in range(1, args.expected + 1)}
    expected_ids.discard(args.poison_id)  # le message empoisonné ne doit jamais être traité

    connection = await connect()
    channel = await connection.channel()
    queue = await channel.declare_queue(RECEIPTS_QUEUE, durable=True)

    receipts: list[dict[str, Any]] = []
    deadline = time.monotonic() + args.timeout
    last_seen = time.monotonic()
    while time.monotonic() < deadline:
        incoming = await queue.get(fail=False, timeout=5)
        if incoming is None:
            done = {r["id"] for r in receipts if r["outcome"] == "ok"}
            if len(done & expected_ids) >= len(expected_ids) and (
                time.monotonic() - last_seen > IDLE_SECONDS
            ):
                break
            await asyncio.sleep(0.5)
            continue
        await incoming.ack()
        last_seen = time.monotonic()
        data = json.loads(incoming.body)
        if str(data["id"]).startswith(args.run_id + "-"):
            receipts.append(data)
    await connection.close()

    ok = sorted((r for r in receipts if r["outcome"] == "ok"), key=lambda r: r["ts"])
    ok_ids = {r["id"] for r in ok}
    gaps = [(b["ts"] - a["ts"], a, b) for a, b in zip(ok, ok[1:], strict=False)]
    max_gap, gap_a, gap_b = max(gaps, key=lambda g: g[0]) if gaps else (0.0, {}, {})
    result: dict[str, Any] = {
        "run_id": args.run_id,
        "expected": len(expected_ids),
        "receipts_ok": len(ok),
        "distinct": len(ok_ids & expected_ids),
        "missing": len(expected_ids - ok_ids),
        "duplicates": len(ok) - len(ok_ids),
        "redelivered_ok": sum(1 for r in ok if r["redelivered"]),
        "pods": sorted({r["pod"] for r in ok}),
        "max_gap_s": round(max_gap, 3),
        "max_gap_start_ts": round(gap_a.get("ts", 0.0), 3),
        "max_gap_end_ts": round(gap_b.get("ts", 0.0), 3),
    }
    if args.delete_ts and ok:
        # Pod le plus ancien = celui supprimé (scénario A) ; le suivant = son remplaçant.
        first_seen: dict[str, float] = {}
        for r in ok:
            first_seen.setdefault(r["pod"], r["ts"])
        pods_by_age = sorted(first_seen, key=lambda p: first_seen[p])
        old_last = max(r["ts"] for r in ok if r["pod"] == pods_by_age[0])
        result["old_pod_last_after_delete_s"] = round(old_last - args.delete_ts, 3)
        if len(pods_by_age) > 1:
            new_first = first_seen[pods_by_age[1]]
            result["new_pod_first_after_delete_s"] = round(new_first - args.delete_ts, 3)
            result["handover_gap_s"] = round(new_first - old_last, 3)
    if args.poison_id:
        attempts = [r for r in receipts if r["id"] == args.poison_id]
        result["poison_attempts"] = len(attempts)
        result["poison_outcomes"] = [r["outcome"] for r in sorted(attempts, key=lambda r: r["ts"])]
    print("RESULT " + json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
