"""Consumer: processes for 20 ms, publishes a receipt to exp.receipts, then acks the message.

Failure rule of contrats.md §3.1: on the first failure, `nack(requeue=True)`; if the message
is already redelivered, `reject(requeue=False)` and a log line.
"""

import asyncio
import json
import os
import time

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from exp.common import PREFETCH, QUEUE, RECEIPTS_QUEUE, connect, declare_topology, log

PROCESSING_SECONDS = 0.02


class ProcessingError(Exception):
    """Deliberate processing failure ("poison" message)."""


async def main() -> None:
    pod = os.environ.get("POD_NAME", "local")
    connection = await connect()
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=PREFETCH)
    receipts = await connection.channel(publisher_confirms=True)
    queue = await declare_topology(channel)

    async def send_receipt(message: AbstractIncomingMessage, outcome: str) -> None:
        receipt = aio_pika.Message(
            body=json.dumps(
                {
                    "id": message.message_id,
                    "ts": time.time(),
                    "pod": pod,
                    "redelivered": message.redelivered,
                    "outcome": outcome,
                }
            ).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await receipts.default_exchange.publish(receipt, routing_key=RECEIPTS_QUEUE)

    async def process(message: AbstractIncomingMessage) -> None:
        await asyncio.sleep(PROCESSING_SECONDS)  # simulated processing
        if json.loads(message.body).get("poison"):
            raise ProcessingError(message.message_id)

    async def handle(message: AbstractIncomingMessage) -> None:
        try:
            try:
                await process(message)
            except ProcessingError:
                if message.redelivered:
                    log("message_rejected", message_id=message.message_id, pod=pod)
                    await send_receipt(message, "rejected")
                    await message.reject(requeue=False)
                else:
                    log("message_requeued", message_id=message.message_id, pod=pod)
                    await send_receipt(message, "failed_requeued")
                    await message.nack(requeue=True)
                return
            await send_receipt(message, "ok")
            await message.ack()  # acknowledgement after processing
        except Exception as exc:  # noqa: BLE001 - no ack: the broker will redeliver the message
            log("handle_failed", message_id=message.message_id, error=type(exc).__name__)

    await queue.consume(handle, no_ack=False)
    log("consumer_start", pod=pod, queue=QUEUE, prefetch=PREFETCH)
    await asyncio.Future()  # runs until the pod is deleted


if __name__ == "__main__":
    asyncio.run(main())
