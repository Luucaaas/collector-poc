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
    args = parser.parse_args()

    connection = await connect()
    channel = await connection.channel()
    queue = await channel.declare_queue(RECEIPTS_QUEUE, durable=True)

    receipts: list[dict[str, Any]] = []
    deadline = time.monotonic() + args.timeout
    last_seen = time.monotonic()
    while time.monotonic() < deadline:
        incoming = await queue.get(fail=False, timeout=5)
        if incoming is None:
            distinct = len({r["id"] for r in receipts})
            if distinct >= args.expected and time.monotonic() - last_seen > IDLE_SECONDS:
                break
            await asyncio.sleep(0.5)
            continue
        await incoming.ack()
        last_seen = time.monotonic()
        data = json.loads(incoming.body)
        if str(data["id"]).startswith(args.run_id + "-"):
            receipts.append(data)
    await connection.close()

    ids = {r["id"] for r in receipts}
    expected_ids = {f"{args.run_id}-{i:05d}" for i in range(1, args.expected + 1)}
    ordered = sorted(receipts, key=lambda r: r["ts"])
    gaps = [(b["ts"] - a["ts"], a, b) for a, b in zip(ordered, ordered[1:], strict=False)]
    max_gap, gap_a, gap_b = max(gaps, key=lambda g: g[0]) if gaps else (0.0, {}, {})
    result: dict[str, Any] = {
        "run_id": args.run_id,
        "expected": args.expected,
        "receipts": len(receipts),
        "distinct": len(ids & expected_ids),
        "missing": len(expected_ids - ids),
        "duplicates": len(receipts) - len(ids),
        "redelivered_flag": sum(1 for r in receipts if r["redelivered"]),
        "pods": sorted({r["pod"] for r in receipts}),
        "max_gap_s": round(max_gap, 3),
        "max_gap_between_pods": [gap_a.get("pod"), gap_b.get("pod")],
    }
    if args.delete_ts:
        after = [r["ts"] for r in ordered if r["ts"] > args.delete_ts]
        if after:
            result["delete_to_first_processed_s"] = round(after[0] - args.delete_ts, 3)
    print("RESULT " + json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
