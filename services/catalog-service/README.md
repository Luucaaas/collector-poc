# catalog-service

Service catalogue de Collector.shop : catégories, boutiques, articles, contrôle automatique et historique des prix. Cette version contient le socle technique (P4-01), les **catégories et boutiques** (P4-02, US-01 et US-02) et les **articles, prix et événements** (P4-03, US-03 et US-04).

Le socle applique déjà les règles du POC :

| Sujet | Mise en oeuvre |
| --- | --- |
| Authentification | JWT RS256 validé localement (`catalog/auth.py`), clés JWKS en cache, un seul titre « Non authentifié » pour tous les 401 |
| Autorisation | dépendance `require_role("seller")` (403 « Accès refusé ») |
| Erreurs | RFC 9457, `application/problem+json`, champ `correlation_id` (`catalog/errors.py`) |
| Corrélation | `X-Request-ID` repris s'il fait au plus 128 caractères de `[A-Za-z0-9._-]`, sinon UUID ; présent dans la réponse et dans chaque log JSON |
| Sondes | `/health/live` (sans dépendance), `/health/ready` (`SELECT 1` sur PostgreSQL, jamais RabbitMQ), `/metrics` |
| Métriques | histogramme de durée aux bornes 0,05 / 0,1 / 0,2 / 0,3 / 0,5 / 1 / 2,5 s : 0,3 s et 0,5 s sont les seuils de l'indicateur I3 |
| Base | SQLAlchemy 2.0 asynchrone (psycopg 3), une session par requête ; Alembic (`0001` vide, `0002` catégories et boutiques, `0003` articles, photos et historique des prix) |
| Unicité des noms | index unique sur `lower(name)` : c'est PostgreSQL qui garantit l'unicité ; une `IntegrityError` devient un 409 `NAME_ALREADY_USED` |
| Coordonnées (RM-02) | `catalog/contact.py`, module pur (emails et téléphones français et internationaux), réutilisé par les articles |

## Routes (P4-02 et P4-03)

| Méthode | Chemin | Rôle | Codes |
| --- | --- | --- | --- |
| GET | `/api/v1/categories` | public | 200 (`items`, `total`, trié par nom) |
| POST | `/api/v1/categories` | `admin` | 201, 401, 403, 409, 422 |
| POST | `/api/v1/shops` | `seller` | 201, 401, 403, 409, 422 (dont `CONTACT_EMAIL`, `CONTACT_PHONE`) |
| GET | `/api/v1/shops/me` | `seller` | 200, 401, 403 |
| GET | `/api/v1/shops/{shop_id}` | public | 200, 404, 422 (identifiant qui n'est pas un UUID) |
| POST | `/api/v1/articles` | `seller`, propriétaire de la boutique | 201 (`PUBLISHED` ou `REJECTED`), 401, 403, 422 (dont `MISSING`, `SHOP_NOT_FOUND`, `CATEGORY_NOT_FOUND`) |
| GET | `/api/v1/articles?category_id=&shop_id=&limit=&offset=` | public, `PUBLISHED` seulement | 200 (`items`, `total`), 422 ; `limit` 20 par défaut, 100 au plus ; tri date décroissante puis `id` |
| GET | `/api/v1/articles/{id}` | public si `PUBLISHED`, sinon propriétaire ou `admin` | 200, 404 (aussi pour un article caché : on ne révèle pas son existence) |
| PUT | `/api/v1/articles/{id}/price` | `seller`, propriétaire | 200, 401, 403, 404 (tiers sur article non publié), 409 (non publié), 422 |
| GET | `/api/v1/articles/{id}/price-history` | propriétaire ou `admin` | 200 (`items`, `total`, ordre chronologique), 401, 403, 404 (aussi tiers sur article non publié) |

Règles : validation RM-01 par Pydantic (montants en chaîne décimale, un nombre JSON est refusé) ; contrôle RM-02 sur le titre et la description (coordonnées : article enregistré `REJECTED`, sans événement) ; prix identique : ni historique ni événement (RM-04). Un verrou de ligne (`SELECT … FOR UPDATE`) sérialise deux modifications de prix concurrentes. Comme FastAPI valide le corps avant d'exécuter la route, un prix invalide sur un article d'un autre vendeur ou inconnu donne 422 avant 403 ou 404.

## Événements (RabbitMQ)

`catalog/events.py` publie `article.published` et `article.price_changed` sur l'exchange `topic` durable `article.events` (contrats.md §3) : messages persistants, confirmation du broker, `message_id` = `event_id`, `type` = type d'événement, en-tête `x-correlation-id` = `X-Request-ID`.

- **Publication juste après le commit**, jamais avant. En cas d'échec, des réessais toutes les 0,5 s pendant `EVENT_PUBLISH_BUDGET_SECONDS` (5 s), puis `event_publish_failed` est journalisé (avec `event_id`) et la réponse reste 201 ou 200 : l'écriture est conservée, l'événement est perdu (limite L2, pas d'*outbox*).
- Le service **démarre sans RabbitMQ** (`amqp_unavailable_at_startup`) et retente la connexion à chaque publication. `/health/ready` ne dépend jamais du broker.
- Un article `REJECTED` n'émet rien.
- Métriques métier dans `/metrics` : `articles_published_total`, `articles_rejected_total{reason}`, `price_changes_total`.

## Prérequis

- Python 3.12 et [uv](https://docs.astral.sh/uv/) ;
- Docker démarré (tests d'intégration par testcontainers : `postgres:18.4-alpine` et `rabbitmq:4.3.5-management`).

## Commandes

Depuis `services/catalog-service` :

```bash
uv sync                                          # installe les versions figées par uv.lock
uv run ruff check                                # lint
uv run ruff format --check                       # format
uv run mypy --strict src                         # typage
uv run pytest --cov=catalog --cov-fail-under=80  # tests unitaires, API, sécurité, intégration
docker build -t catalog-service .                # image non-root
```

Lancement local (base PostgreSQL déjà disponible) :

```bash
cp .env.example .env   # puis adapter DATABASE_URL ; .env est ignoré par git
set -a; source .env; set +a
uv run alembic upgrade head
uv run uvicorn --factory catalog.main:create_app --port 8000
```

Les tests génèrent eux-mêmes leurs clés RSA et un JWKS de test : ni Keycloak ni clé versionnée.

## Variables d'environnement

| Variable | Obligatoire | Défaut | Rôle |
| --- | --- | --- | --- |
| `DATABASE_URL` | oui | | URL SQLAlchemy, `postgresql+psycopg://utilisateur:mot-de-passe@hôte/catalog_db` (Secret Kubernetes) |
| `RABBITMQ_URL` | oui | | URL AMQP, `amqp://utilisateur:mot-de-passe@hôte:5672/` (Secret Kubernetes) |
| `EVENT_PUBLISH_BUDGET_SECONDS` | non | `5` | durée totale (réessais compris) accordée à la publication d'un événement |
| `ISSUER` | non | `https://auth.127.0.0.1.sslip.io/realms/collector` | valeur attendue de `iss` (URL publique de Keycloak) |
| `JWKS_URL` | non | URL interne du Service Keycloak (`…/protocol/openid-connect/certs`) | récupération des clés publiques |
| `AUDIENCE` | non | `collector-api` | valeur attendue de `aud` |
| `CORS_ORIGIN` | non | `https://app.127.0.0.1.sslip.io` | seule origine autorisée par CORS |
| `JWKS_TTL_SECONDS` | non | `600` | durée de vie du cache des clés |
| `JWKS_MIN_REFETCH_SECONDS` | non | `30` (au moins 1, sinon le service refuse de démarrer) | délai minimal entre deux rechargements sur `kid` inconnu |
| `JWKS_MAX_STALE_SECONDS` | non | `3600` | durée pendant laquelle les clés périmées restent utilisées si Keycloak ne répond pas (au-delà du TTL) |
| `JWKS_TIMEOUT_SECONDS` | non | `2` | délai d'attente de Keycloak pour le JWKS (strictement positif) |
| `DB_CONNECT_TIMEOUT_SECONDS` | non | `3` | délai de connexion à PostgreSQL |
| `LOG_LEVEL` | non | `INFO` | niveau de log |

## Structure

```
src/catalog/   config, logging, correlation (middleware), errors, auth, db, health, metrics, main (create_app),
               models, categories, shops, articles, events, contact, slug, persistence
migrations/    Alembic (env.py lit DATABASE_URL)
tests/         test_unit, test_contact_slug, test_security, test_api_catalog (acceptation US-01 et US-02),
               test_articles_unit, test_api_articles (acceptation US-03 et US-04), event_schemas (schémas du
               contrat), test_rabbitmq (vrai RabbitMQ), test_integration (testcontainers)
```

## Ajouter une route

Créer un `APIRouter` préfixé `/api/v1`, l'inclure dans `create_app()`, protéger par `Depends(get_current_user)` ou `Depends(require_role("seller"))`, utiliser `ApiModel` (`extra="forbid"`) pour les corps, `ProblemError` pour les erreurs métier, et `Depends(get_session)` pour la base.

## Limites connues

- Les lignes de démarrage et d'arrêt d'uvicorn (`INFO: …`) ne sont pas en JSON ; tous les logs applicatifs le sont.
- Sur macOS, le fichier `.pth` de l'installation éditable peut être marqué « caché » : `python` ou `uvicorn` échouent alors avec `ModuleNotFoundError: catalog`. Pytest n'en dépend plus (`pythonpath = ["src"]`) ; sinon lancer `uv sync --reinstall-package catalog-service`.
- Contrôle des coordonnées : les formes obfusquées ne sont pas détectées (RM-02), ni un numéro collé à d'autres chiffres sans séparateur (« 106 12 34 56 78 »). Méthode et cas couverts : docstring de `src/catalog/contact.py`. Un nom de catégorie sans lettre ni chiffre, ou dont le slug dépasse 120 caractères, est refusé en 422 `NAME_INVALID`.
- `GET /shops/{shop_id}` avec un identifiant qui n'est pas un UUID répond 422 (validation FastAPI), pas 404.
- La description d'une boutique est facultative, limitée à 1 000 caractères ; une description vide est enregistrée `null`.
- `GET /categories` et `GET /shops/me` ne sont pas paginées.
- Un article n'a qu'une opération de modification (le prix) ; pas de suppression ni d'édition du texte. `shipping_fee` est obligatoire (422 `MISSING`) ; la devise vaut `EUR` si omise.
- Pas de tests de charge ni d'acceptation ici (phases 4 P4-05 et 8).
