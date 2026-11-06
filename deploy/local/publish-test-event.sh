#!/usr/bin/env bash
# Publie un événement de test `article.published` (schema_version 1) sur l'exchange `article.events`
# du cluster k3d, puis vérifie que notification-service l'a consommé.
#
# Usage : deploy/local/publish-test-event.sh
#
# - Le compte RabbitMQ utilisé est `catalog`. Ses droits (deploy/compose/render.py) : configure et
#   write sur l'exchange `article.events` seulement, read vide (aucune lecture), aucune étiquette
#   d'administration. Son mot de passe est lu dans
#   deploy/local/.env et transmis par l'ENTRÉE STANDARD de `kubectl exec` : jamais en argument de
#   commande (`ps` le montrerait), jamais affiché, jamais écrit dans un fichier.
# - La publication se fait en AMQP depuis un pod de catalog-service (aio-pika y est installé) : le
#   compte `catalog` n'a pas le droit d'utiliser l'API HTTP de gestion de RabbitMQ.
# - La catégorie de l'événement n'existe pas : aucun acheteur n'est notifié, mais l'événement est
#   bien consommé (`events_consumed_total{outcome="processed"}`), ce qui prouve la chaîne
#   RabbitMQ -> notification-service sans client Keycloak.
# - Avant et après, le script lit ce compteur dans chaque pod de notification-service (somme).
set -euo pipefail

CLUSTER="collector"
K="kubectl --context k3d-${CLUSTER} -n collector"
HERE="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${HERE}/.env"

# Somme, sur tous les pods de notification-service, du compteur des événements traités. La
# métrique est lue DANS le pod (le port de l'application n'est pas exposé hors du cluster).
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

[[ -f "$ENV_FILE" ]] || { echo "Fichier ${ENV_FILE} absent : lancer 'deploy/local/deploy.sh infra' d'abord." >&2; exit 1; }
password="$(grep '^RABBITMQ_CATALOG_PASSWORD=' "$ENV_FILE" | head -n 1 | cut -d= -f2- || true)"
[[ -n "$password" ]] || { echo "RABBITMQ_CATALOG_PASSWORD absent ou vide dans ${ENV_FILE}." >&2; exit 1; }

correlation_id="test-event-$(date +%Y%m%d%H%M%S)"
before="$(processed_total)"
echo "Événements traités avant : ${before}"

# Programme Python exécuté dans le pod : lit le mot de passe sur l'entrée standard, publie, affiche
# seulement l'identifiant de l'événement. Il ne contient aucun secret.
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
            "title": "Article de test du déploiement",
            "price": "12.00",
            "shipping_fee": "3.00",
            "currency": "EUR",
        },
    }
    # Aucune exception n est affichee telle quelle : le message de certaines contient la
    # chaine de connexion AMQP, donc le mot de passe. Seul le type de l erreur est affiche.
    try:
        connection = await aio_pika.connect(f"amqp://catalog:{password}@rabbitmq:5672/", timeout=10)
    except Exception as exc:
        print("Connexion à RabbitMQ impossible :", type(exc).__name__, file=sys.stderr)
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
    print("Publié :", event["event_id"], "(correlation_id", correlation_id + ")")

try:
    asyncio.run(main(sys.argv[1]))
except SystemExit:
    raise
except Exception as exc:
    print("Publication impossible :", type(exc).__name__, file=sys.stderr)
    sys.exit(1)
'
# printf est une commande interne du shell : le mot de passe ne figure dans aucun argument de processus.
printf '%s\n' "$password" | $K exec -i deploy/catalog-service -- python -c "$program" "$correlation_id"
unset password

# Le consommateur traite l'événement en quelques centaines de millisecondes ; on attend jusqu'à 20 s.
after="$before"
for _ in $(seq 1 20); do
  after="$(processed_total)"
  [[ "$after" -gt "$before" ]] && break
  sleep 1
done
echo "Événements traités après : ${after}"
if [[ "$after" -gt "$before" ]]; then
  echo "OK : l'événement a été consommé par notification-service (+$((after - before)))."
else
  echo "ECHEC : le compteur n'a pas augmenté." >&2
  exit 1
fi
