"""Producteur : publie N messages numérotés, persistants, avec confirmation du broker."""

import argparse
import asyncio
import json
import time

import aio_pika

from exp.common import EXCHANGE, ROUTING_KEY, connect, declare_topology, log

PUBLISH_TIMEOUT = 5.0


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--rate", type=float, default=50.0)
    args = parser.parse_args()

    connection = await connect()
    channel = await connection.channel(publisher_confirms=True)
    await declare_topology(channel)
    exchange = await channel.get_exchange(EXCHANGE)

    log("producer_start", run_id=args.run_id, count=args.count, rate=args.rate)
    max_outage = 0.0
    retries = 0
    started = time.monotonic()
    for i in range(1, args.count + 1):
        message_id = f"{args.run_id}-{i:05d}"
        message = aio_pika.Message(
            body=json.dumps({"n": i}).encode(),
            message_id=message_id,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        first_failure: float | None = None
        while True:
            try:
                await exchange.publish(message, routing_key=ROUTING_KEY, timeout=PUBLISH_TIMEOUT)
                break
            except Exception as exc:  # noqa: BLE001 - tout échec = on republie le même message
                retries += 1
                if first_failure is None:
                    first_failure = time.monotonic()
                    log("publish_failed", message_id=message_id, error=type(exc).__name__)
                await asyncio.sleep(0.5)
        if first_failure is not None:
            outage = time.monotonic() - first_failure
            max_outage = max(max_outage, outage)
            log("publish_recovered", message_id=message_id, outage_s=round(outage, 3))
        if i % 100 == 0:
            log("progress", confirmed=i)
        # cadence : le i-ième message est dû à started + i / rate
        delay = started + i / args.rate - time.monotonic()
        if delay > 0:
            await asyncio.sleep(delay)

    log(
        "producer_done",
        run_id=args.run_id,
        confirmed=args.count,
        retries=retries,
        max_outage_s=round(max_outage, 3),
    )
    await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
