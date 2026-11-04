# Tests d'acceptation

17 tests de bout en bout, **un par critère d'acceptation** de [`docs/03-backlog/user-stories.md`](../../docs/03-backlog/user-stories.md), nommés `test_usXX_caY_<description>`. Ils traversent les deux services, PostgreSQL, RabbitMQ et Keycloak : pytest + httpx pour l'API, aio-pika pour observer les événements sur une file temporaire liée à `article.events`.

| Fichier | Story | Tests |
| --- | --- | --- |
| `test_us01_categories.py` | US-01 Créer une catégorie | CA1 à CA3 |
| `test_us02_boutiques.py` | US-02 Créer une boutique | CA1 à CA3 |
| `test_us03_publication.py` | US-03 Publier un article | CA1 à CA4 |
| `test_us04_prix.py` | US-04 Modifier le prix | CA1 à CA3 |
| `test_us05_notifications.py` | US-05 Intérêts et notifications | CA1 à CA4 |

## Lancer

```bash
deploy/compose/up.sh                                   # pile locale (une fois)
cd tests/acceptance
uv run pytest --junitxml=junit.xml                     # 17 tests
deploy/compose/down.sh --volumes                       # tout supprimer
```

Les jetons des comptes `admin`, `alice`, `bob` et `chloe` sont obtenus auprès de Keycloak par le client `collector-tests` (*Direct Access Grants*), qui n'existe que dans la pile `docker compose`. Les mots de passe sont lus dans `deploy/compose/.env` (généré par `up.sh`, ignoré par git).

## Configuration (variables d'environnement)

| Variable | Défaut |
| --- | --- |
| `ACCEPTANCE_CATALOG_URL` | `http://localhost:8001` |
| `ACCEPTANCE_NOTIFICATION_URL` | `http://localhost:8002` |
| `ACCEPTANCE_KEYCLOAK_URL` | `http://localhost:8080` |
| `ACCEPTANCE_AMQP_HOST` | `localhost:5672` (utilisateur `admin` de RabbitMQ) |
| `ACCEPTANCE_AMQP_URL` | construite à partir de `.env` et de `ACCEPTANCE_AMQP_HOST` |
| `ACCEPTANCE_ENV_FILE` | `deploy/compose/.env` |

## Rejouables

Chaque test crée ses données avec un suffixe aléatoire (catégories, boutiques, titres) et ne dépend ni de l'ordre ni d'un état préexistant : la suite repasse sur une pile qui garde les données d'une exécution précédente. Les comptes `alice` et `chloe` fixent leurs centres d'intérêt au début de chaque test qui en a besoin.

## Vérifications de qualité

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy .
```
