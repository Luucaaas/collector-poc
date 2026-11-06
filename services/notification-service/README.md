# notification-service

Service de notifications de Collector.shop : **centres d'intérêt et préférences** des acheteurs (API REST), **consommation** des événements `article.published` et `article.price_changed` de RabbitMQ, et **notifications** des acheteurs intéressés (US-05). Il ferme la boucle métier du POC : vendeur → contrôle → événement → acheteur notifié.

## Origine du socle

Le socle technique (configuration, logs JSON, RFC 9457, `X-Request-ID`, authentification JWT et cache JWKS, `require_role`, sondes, métriques, accès PostgreSQL, Alembic, Dockerfile) est **recopié de `catalog-service`**, et non partagé dans une bibliothèque : chaque service se construit, se teste et se déploie seul, avec les mêmes versions (`uv.lock` identique, au nom du projet près). **Toute correction du socle se fait dans les deux services.** Fichiers recopiés : `auth.py`, `correlation.py`, `errors.py`, `health.py`, `schemas.py` (identiques à ceux du catalogue au nom du paquet près), `db.py`, `migrations/env.py`, `Dockerfile`, `.dockerignore`, et les tests `test_security.py` et `test_unit.py`. `test_integration.py` reprend ceux du socle sur les sondes et la base ; les tests de migration sont dans `test_migrations.py`.

**Différences avec le socle de `catalog-service`** (liste exhaustive des fichiers recopiés qui divergent) :

| Fichier | Différence | Raison |
| --- | --- | --- |
| `config.py` | `event_publish_budget_seconds` retiré ; `consumer_prefetch` (10) et `amqp_retry_seconds` (1 s) ajoutés | ce service consomme au lieu de publier |
| `metrics.py` | `BusinessMetrics` : `notifications_created_total{type}`, `events_consumed_total{event_type, outcome}` et `notification_delay_seconds{event_type}` à la place des compteurs d'articles | métriques métier propres au service (contrats.md §2.3) |
| `db.py` | seul le commentaire de `Base` change | les modèles existent désormais |
| `main.py` | spécifique au service (non recopié tel quel) : routeur `/me`, consommateur dans le lifespan, CORS sans `POST` | pas de publication ni de route d'écriture en `POST` |

## Routes (contrats.md §2.2)

Toutes exigent le rôle `buyer` ; l'utilisateur est le `sub` du jeton (aucun identifiant d'utilisateur dans l'URL).

| Méthode | Chemin | Codes |
| --- | --- | --- |
| GET | `/api/v1/me/interests` | 200, 401, 403 |
| PUT | `/api/v1/me/interests` | 200, 401, 403, 422 |
| GET | `/api/v1/me/preferences` | 200, 401, 403 |
| PUT | `/api/v1/me/preferences` | 200, 401, 403, 422 |
| GET | `/api/v1/me/notifications?limit=&offset=` | 200, 401, 403, 422 |

- `PUT /me/interests` **remplace la liste entière** : `{"category_ids": ["<uuid>", …]}`. Les identifiants sont dédoublonnés. La liste dédoublonnée compte au plus 20 identifiants, sinon 422 (`TOO_MANY_CATEGORIES`) : 21 identifiants dont un doublon sont acceptés. Une liste brute de plus de 200 identifiants est refusée (borne technique). Le format UUID est vérifié, pas l'existence de la catégorie : ce service n'appelle jamais le catalogue (ADR 0001). Deux remplacements simultanés du même acheteur sont sérialisés par un verrou consultatif (`pg_advisory_xact_lock`).
- `/me/preferences` : `{"new_article": true, "price_changed": false}`, deux booléens stricts obligatoires. Sans préférences enregistrées, les deux types sont actifs.
- `GET /me/notifications` : `{"items": [...], "total": n}`, `limit` 20 par défaut (100 au plus), de la plus récente à la plus ancienne. Un élément : `id`, `type` (`NEW_ARTICLE` ou `PRICE_CHANGED`), `article_id`, `content`, `created_at`.
  - `NEW_ARTICLE` : `content = {"title", "price", "currency"}`.
  - `PRICE_CHANGED` : `content = {"title", "old_price", "new_price", "currency"}`.
  - Les montants sont des chaînes décimales (`"120.00"`).

## Consommateur RabbitMQ (`consumer.py`, `events.py`)

Lancé dans le lifespan de l'application (même processus), arrêté proprement à l'arrêt. Il déclare l'exchange `topic` durable `article.events` et la file durable `notification.article-events`, liée par `article.*`. `prefetch = 10`.

- **Démarrage sans RabbitMQ** : la connexion est tentée en tâche de fond (toutes les secondes), le service démarre et `/health/ready` reste à 200 (la sonde ne teste que PostgreSQL). Une fois connecté, `aio-pika` se reconnecte seul.
- **Lecteur tolérant** (contrats.md §3.3) : les champs inconnus de l'enveloppe et de `data` sont ignorés, les champs connus restent exigés avec leur type. Un `event_type` inconnu mais d'enveloppe valide est acquitté sans traitement (`event_ignored`, `outcome="ignored"`). Les schémas JSON stricts du contrat décrivent ce que le producteur émet.
- **Traitement d'un événement** : validation de `data` (champs de contrats.md §3.4 et §3.5), calcul des destinataires en une requête (intérêt sur la catégorie, préférence du type concerné vraie par défaut, vendeur exclu : RM-08), insertion de toutes les notifications en une transaction avec `ON CONFLICT DO NOTHING` sur `(user_id, source_event_id)` (RM-09), puis **acquittement après le commit**. `correlation_id` et `event_id` de l'événement figurent dans les logs.
- **Règle d'échec** (contrats.md §3.1) : un message dont le traitement échoue est remis en file une fois (`message_requeued`), puis rejeté sans remise et journalisé (`message_rejected`, avec `event_id`). Un message invalide (JSON invalide, champ requis absent ou mal typé, `schema_version` inconnue pour un type connu) est rejeté sans remise dès la première fois. Il n'y a pas de *dead-letter queue* dans le POC (cible).
- **Limites assumées** : un message redélivré après une coupure de connexion est traité comme « deuxième tentative » (L21) ; la remise en file est immédiate, donc une panne brève de PostgreSQL peut faire rejeter des événements (L22). Voir `architecture-poc.md` §8.

## Métriques

En plus des métriques HTTP (histogramme aux bornes de l'indicateur I3) :

- `notifications_created_total{type}` ;
- `events_consumed_total{event_type, outcome}` avec `outcome` = `processed`, `requeued`, `rejected`, `invalid` ou `ignored` (`event_type="unknown"` pour un message invalide ou ignoré) ;
- `notification_delay_seconds{event_type}` : histogramme du délai entre `occurred_at` et la disponibilité des notifications (après le commit), observé une fois par événement ayant créé au moins une notification (ENF-14, p95 < 2 s). Bornes 0,1 / 0,25 / 0,5 / 1 / 2 / 5 / 10 s : le seuil de 2 s est une borne, sans interpolation. Un délai négatif (horloges décalées) est ramené à 0 et signalé par le log `negative_notification_delay`.

## Prérequis

- Python 3.12 et [uv](https://docs.astral.sh/uv/) ;
- Docker démarré (tests par testcontainers : `postgres:18.4-alpine` et `rabbitmq:4.3.5-management`).

## Commandes

Depuis `services/notification-service` :

```bash
uv sync                                              # installe les versions figées par uv.lock
uv run ruff check                                    # lint
uv run ruff format --check                           # format
uv run mypy --strict src                             # typage
uv run pytest --cov=notification --cov-fail-under=80 # unitaires, API, sécurité, RabbitMQ, intégration
docker build -t notification-service .               # image non-root
```

Lancement local (PostgreSQL et RabbitMQ déjà disponibles) :

```bash
cp .env.example .env   # puis adapter DATABASE_URL et RABBITMQ_URL ; .env est ignoré par git
set -a; source .env; set +a
uv run alembic upgrade head
uv run uvicorn --factory notification.main:create_app --port 8000
```

Les tests génèrent eux-mêmes leurs clés RSA et un JWKS de test : ni Keycloak ni clé versionnée.

## Variables d'environnement

| Variable | Obligatoire | Défaut | Rôle |
| --- | --- | --- | --- |
| `DATABASE_URL` | oui | | URL SQLAlchemy, `postgresql+psycopg://utilisateur:mot-de-passe@hôte/notification_db` (Secret Kubernetes) |
| `RABBITMQ_URL` | oui | | URL AMQP, `amqp://utilisateur:mot-de-passe@hôte:5672/` (Secret Kubernetes) |
| `CONSUMER_PREFETCH` | non | `10` | messages non acquittés confiés au consommateur |
| `AMQP_RETRY_SECONDS` | non | `1` | délai entre deux tentatives de connexion au broker |
| `ISSUER` | non | `https://auth.127.0.0.1.sslip.io/realms/collector` | valeur attendue de `iss` (URL publique de Keycloak) |
| `JWKS_URL` | non | URL interne du Service Keycloak (`…/protocol/openid-connect/certs`) | récupération des clés publiques |
| `AUDIENCE` | non | `collector-api` | valeur attendue de `aud` |
| `CORS_ORIGIN` | non | `https://app.127.0.0.1.sslip.io` | seule origine autorisée par CORS |
| `JWKS_TTL_SECONDS` | non | `600` | durée de vie du cache des clés |
| `JWKS_MIN_REFETCH_SECONDS` | non | `30` (au moins 1) | délai minimal entre deux rechargements sur `kid` inconnu |
| `JWKS_MAX_STALE_SECONDS` | non | `3600` | durée pendant laquelle les clés périmées restent utilisées si Keycloak ne répond pas |
| `JWKS_TIMEOUT_SECONDS` | non | `2` | délai d'attente de Keycloak pour le JWKS |
| `DB_CONNECT_TIMEOUT_SECONDS` | non | `3` | délai de connexion à PostgreSQL |
| `LOG_LEVEL` | non | `INFO` | niveau de log |

## Structure

```
src/notification/   config, logging, correlation (middleware), errors, auth, db, health, metrics, main (create_app),
                    models, me (routes /me/*), events (validation, contenu, destinataires), consumer (RabbitMQ)
migrations/         Alembic (0001 : interests, preferences, notifications)
tests/              test_events_unit, test_processing (destinataires, RM-08 et RM-09), test_api_notifications
                    (acceptation CA1 et CA4), test_rabbitmq (CA2 et CA3, doublon, message empoisonné, démarrage sans
                    broker), test_migrations, test_integration, test_security, test_unit, factory + event_schemas
                    (événements de test validés contre les schémas du contrat)
```

## Limites connues

- L'index `ix_interests_category_id` complète la clé primaire `(user_id, category_id)` (contrats.md §4.2) : sans lui, la recherche des destinataires d'une catégorie parcourrait toute la table.
- Pas d'envoi d'email ni de notification poussée (cible). Pas de lecture ni de suppression des notifications.
- Pas de *dead-letter queue* ni de rejeu : un message rejeté n'est que journalisé (cible : DLQ).
- Tant que le broker est absent, `aiormq` écrit une ligne ERROR (en JSON) à chaque tentative de connexion, soit une par `AMQP_RETRY_SECONDS` ; le service, lui, n'écrit qu'un `amqp_unavailable`.
- Sur macOS, le fichier `.pth` de l'installation éditable peut être marqué « caché » : `uvicorn` échoue alors avec `ModuleNotFoundError: notification`. Pytest n'en dépend pas (`pythonpath = ["src"]`) ; sinon lancer `uv sync --reinstall-package notification-service`.
- Pas de tests de charge ni d'acceptation de bout en bout ici (P4-05 et phase 8).
