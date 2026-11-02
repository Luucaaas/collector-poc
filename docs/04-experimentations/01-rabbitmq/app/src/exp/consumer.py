"""Consommateur : traite 20 ms, publie un accusé dans exp.receipts, puis acquitte le message."""

import asyncio
import json
import os
import time

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from exp.common import PREFETCH, QUEUE, RECEIPTS_QUEUE, connect, declare_topology, log

PROCESSING_SECONDS = 0.02


async def main() -> None:
    pod = os.environ.get("POD_NAME", "local")
    connection = await connect()
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=PREFETCH)
    receipts = await connection.channel(publisher_confirms=True)
    queue = await declare_topology(channel)

    async def handle(message: AbstractIncomingMessage) -> None:
        try:
            await asyncio.sleep(PROCESSING_SECONDS)  # traitement simulé
            receipt = aio_pika.Message(
                body=json.dumps(
                    {
                        "id": message.message_id,
                        "ts": time.time(),
                        "pod": pod,
                        "redelivered": message.redelivered,
                    }
                ).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await receipts.default_exchange.publish(receipt, routing_key=RECEIPTS_QUEUE)
            await message.ack()  # acquittement après traitement
        except Exception as exc:  # noqa: BLE001 - sans ack, le broker relivrera le message
            log("handle_failed", message_id=message.message_id, error=type(exc).__name__)

    await queue.consume(handle, no_ack=False)
    log("consumer_start", pod=pod, queue=QUEUE, prefetch=PREFETCH)
    await asyncio.Future()  # tourne jusqu'à la suppression du pod


if __name__ == "__main__":
    asyncio.run(main())
