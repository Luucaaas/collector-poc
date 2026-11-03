# catalog-service

Service catalogue de Collector.shop : catégories, boutiques, articles, contrôle automatique et historique des prix. Cette version est le **socle technique** (tâche P4-01) : aucune route métier. Les routes arrivent avec P4-02 et P4-03.

Le socle applique déjà les règles du POC :

| Sujet | Mise en oeuvre |
| --- | --- |
| Authentification | JWT RS256 validé localement (`catalog/auth.py`), clés JWKS en cache, un seul titre « Non authentifié » pour tous les 401 |
| Autorisation | dépendance `require_role("seller")` (403 « Accès refusé ») |
| Erreurs | RFC 9457, `application/problem+json`, champ `correlation_id` (`catalog/errors.py`) |
| Corrélation | `X-Request-ID` repris s'il fait au plus 128 caractères de `[A-Za-z0-9._-]`, sinon UUID ; présent dans la réponse et dans chaque log JSON |
| Sondes | `/health/live` (sans dépendance), `/health/ready` (`SELECT 1` sur PostgreSQL, jamais RabbitMQ), `/metrics` |
| Métriques | histogramme de durée aux bornes 0,05 / 0,1 / 0,2 / 0,3 / 0,5 / 1 / 2,5 s : 0,3 s et 0,5 s sont les seuils de l'indicateur I3 |
| Base | SQLAlchemy 2.0 asynchrone (psycopg 3), une session par requête ; Alembic (migration `0001` vide) |

## Prérequis

- Python 3.12 et [uv](https://docs.astral.sh/uv/) ;
- Docker démarré (tests d'intégration par testcontainers, image `postgres:18.4-alpine`).

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
| `ISSUER` | non | `https://auth.127.0.0.1.sslip.io/realms/collector` | valeur attendue de `iss` (URL publique de Keycloak) |
| `JWKS_URL` | non | URL interne du Service Keycloak (`…/protocol/openid-connect/certs`) | récupération des clés publiques |
| `AUDIENCE` | non | `collector-api` | valeur attendue de `aud` |
| `CORS_ORIGIN` | non | `https://app.127.0.0.1.sslip.io` | seule origine autorisée par CORS |
| `JWKS_TTL_SECONDS` | non | `600` | durée de vie du cache des clés |
| `JWKS_MIN_REFETCH_SECONDS` | non | `30` | délai minimal entre deux rechargements sur `kid` inconnu |
| `JWKS_MAX_STALE_SECONDS` | non | `3600` | durée pendant laquelle les clés périmées restent utilisées si Keycloak ne répond pas (au-delà du TTL) |
| `DB_CONNECT_TIMEOUT_SECONDS` | non | `3` | délai de connexion à PostgreSQL |
| `LOG_LEVEL` | non | `INFO` | niveau de log |

## Structure

```
src/catalog/   config, logging, correlation (middleware), errors, auth, db, health, metrics, main (create_app)
migrations/    Alembic (env.py lit DATABASE_URL)
tests/         test_unit, test_security, test_integration (testcontainers)
```

## Ajouter une route (P4-02 et suivantes)

Créer un `APIRouter` préfixé `/api/v1`, l'inclure dans `create_app()`, protéger par `Depends(get_current_user)` ou `Depends(require_role("seller"))`, utiliser `ApiModel` (`extra="forbid"`) pour les corps, `ProblemError` pour les erreurs métier, et `Depends(get_session)` pour la base.

## Limites connues

- Les lignes de démarrage et d'arrêt d'uvicorn (`INFO: …`) ne sont pas en JSON ; tous les logs applicatifs le sont.
- Pas de tests de charge ni d'acceptation ici (phases 4 P4-05 et 8).
