#!/usr/bin/env bash
# Publishes a test `article.published` event (schema_version 1) on the `article.events` exchange
# of the k3d cluster, then checks that notification-service consumed it.
#
# Usage: deploy/local/publish-test-event.sh
#
# - The RabbitMQ account used is `catalog`. Its permissions (deploy/compose/render.py): configure and
#   write on the `article.events` exchange only, empty read (no reading), no administration
#   tag. Its password is read from
#   deploy/local/.env and passed through the STANDARD INPUT of `kubectl exec`: never as a command
#   argument (`ps` would show it), never printed, never written to a file.
# - Publishing is done over AMQP from a catalog-service pod (aio-pika is installed there): the
#   `catalog` account is not allowed to use the RabbitMQ HTTP management API.
# - The event's category does not exist: no buyer is notified, but the event is
#   consumed all the same (`events_consumed_total{outcome="processed"}`), which proves the
#   RabbitMQ -> notification-service chain without a Keycloak client.
# - Before and after, the script reads this counter in each notification-service pod (sum).
set -euo pipefail

CLUSTER="collector"
K="kubectl --context k3d-${CLUSTER} -n collector"
HERE="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${HERE}/.env"

# Sum, over all notification-service pods, of the processed-events counter. The
# metric is read INSIDE the pod (the application port is not exposed outside the cluster).
processed_total() {
  local pod value total=0
  for pod in $($K get pods -l app.kubernetes.io/name=notification-service -o jsonpath='{.items[*].metadata.name}'); do
    value="$($K exec "$pod" -- python -c '
import re, urllib.request
text = urllib.request.urlopen("http://localhost:8000/metrics").read().decode()
m = re.search(r"^events_consumed_total\{[^}]*outcome=\"processed\"[^}]*\} (\S+)", text, re.M)
print(int(float(m.group(1))) if m else 0)')"
    total=$((total + value))
  done
  echo "$total"
}

[[ -f "$ENV_FILE" ]] || { echo "File ${ENV_FILE} missing: run 'deploy/local/deploy.sh infra' first." >&2; exit 1; }
password="$(grep '^RABBITMQ_CATALOG_PASSWORD=' "$ENV_FILE" | head -n 1 | cut -d= -f2- || true)"
[[ -n "$password" ]] || { echo "RABBITMQ_CATALOG_PASSWORD missing or empty in ${ENV_FILE}." >&2; exit 1; }

correlation_id="test-event-$(date +%Y%m%d%H%M%S)"
before="$(processed_total)"
echo "Events processed before: ${before}"

# Python program run in the pod: reads the password on standard input, publishes, prints
# only the event identifier. It contains no secret.
program='
import asyncio, json, sys, uuid
from datetime import datetime, timezone
import aio_pika

async def main(correlation_id):
    password = sys.stdin.readline().strip()
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "article.published",
        "schema_version": 1,
        "occurred_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "producer": "catalog-service",
        "correlation_id": correlation_id,
        "data": {
            "article_id": str(uuid.uuid4()),
            "shop_id": str(uuid.uuid4()),
            "seller_id": "test-seller",
            "category_id": str(uuid.uuid4()),
            "title": "Deployment test article",
            "price": "12.00",
            "shipping_fee": "3.00",
            "currency": "EUR",
        },
    }
    # No exception is printed as is: the message of some of them contains the
    # AMQP connection string, hence the password. Only the error type is printed.
    try:
        connection = await aio_pika.connect(f"amqp://catalog:{password}@rabbitmq:5672/", timeout=10)
    except Exception as exc:
        print("Cannot connect to RabbitMQ:", type(exc).__name__, file=sys.stderr)
        sys.exit(1)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.get_exchange("article.events", ensure=False)
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(event).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                message_id=event["event_id"],
                type=event["event_type"],
                headers={"x-correlation-id": correlation_id},
            ),
            routing_key="article.published",
        )
    print("Published:", event["event_id"], "(correlation_id", correlation_id + ")")

try:
    asyncio.run(main(sys.argv[1]))
except SystemExit:
    raise
except Exception as exc:
    print("Cannot publish:", type(exc).__name__, file=sys.stderr)
    sys.exit(1)
'
# printf is a shell builtin: the password does not appear in any process argument.
printf '%s\n' "$password" | $K exec -i deploy/catalog-service -- python -c "$program" "$correlation_id"
unset password

# The consumer processes the event in a few hundred milliseconds; we wait up to 20 s.
after="$before"
for _ in $(seq 1 20); do
  after="$(processed_total)"
  [[ "$after" -gt "$before" ]] && break
  sleep 1
done
echo "Events processed after: ${after}"
if [[ "$after" -gt "$before" ]]; then
  echo "OK: the event was consumed by notification-service (+$((after - before)))."
else
  echo "FAILURE: the counter did not increase." >&2
  exit 1
fi
