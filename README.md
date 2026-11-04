# Collector.shop — POC

Prototype de la plateforme Collector.shop (vente d'objets de collection entre particuliers), réalisé dans le cadre du bloc CESI MAALSI « Superviser et assurer le développement des applications logicielles ».

## Fonctionnalité métier

Un vendeur publie un article ou modifie son prix → contrôle automatique → un événement est publié sur RabbitMQ → les acheteurs intéressés sont notifiés. Un outil anti-fraude pourra s'abonner aux mêmes événements sans modifier le catalogue.

## Stack

| Couche | Technologies |
| --- | --- |
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic, aio-pika |
| Front | React, TypeScript, Vite, MUI |
| Données et messaging | PostgreSQL, RabbitMQ |
| Sécurité | Keycloak (OIDC + PKCE), TLS par Traefik (certificat mkcert), SonarCloud, Trivy |
| Plateforme | Docker, Kubernetes local (k3d), Traefik, Helm (déploiement par script) |
| CI/CD et qualité | GitHub Actions, GHCR, SonarCloud |
| Observabilité | Prometheus, Grafana |

## Organisation du repo

```
docs/        Processus qualité, architecture, backlog, expérimentations, compétences, sécurité
services/    Services backend FastAPI (catalog, notification)
frontend/    Application React
tests/       Tests d'acceptation et de charge
deploy/      Cluster local, infrastructure Helm, chart générique des services, script de déploiement
.github/     Pipelines CI/CD
```

## Lancer le POC en local

Pile `docker compose` : PostgreSQL, RabbitMQ, Keycloak (realm `collector`) et les deux services. Elle sert aux tests d'acceptation et à la CI ; le déploiement sur le cluster k3d (phase 6) viendra s'y ajouter.

**Prérequis** : Docker Desktop démarré, [uv](https://docs.astral.sh/uv/) et Python 3. Ports libres sur `127.0.0.1` : 5672, 8001, 8002, 8080, 15672.

```bash
deploy/compose/up.sh                     # génère .env (mots de passe aléatoires), construit les images, démarre et attend les sondes
cd tests/acceptance && uv run pytest     # 17 tests d'acceptation, un par critère du backlog
deploy/compose/down.sh --volumes         # arrête la pile et supprime les données
```

`up.sh` ne réécrit jamais `.env`. Sans `--volumes`, `down.sh` garde les données pour le prochain lancement.

| Service | URL |
| --- | --- |
| catalog-service | http://localhost:8001/api/v1/categories (documentation : `/api/v1/docs`) |
| notification-service | http://localhost:8002/api/v1/me/notifications (jeton requis) |
| Keycloak | http://localhost:8080 (realm `collector`) |
| RabbitMQ (management) | http://localhost:15672 (utilisateur `admin`) |

**Comptes de démonstration** (mots de passe dans `deploy/compose/.env`) : `admin` (rôle `admin`), `alice` (`seller` et `buyer`), `bob` (`seller`), `chloe` (`buyer`).

**Exemple : obtenir un jeton et appeler l'API.** Le client `collector-tests` (flux *Direct Access Grants*) n'existe que dans cette pile, pour obtenir un jeton sans navigateur.

```bash
set -a; source deploy/compose/.env; set +a
TOKEN=$(curl -s http://localhost:8080/realms/collector/protocol/openid-connect/token \
  -d grant_type=password -d client_id=collector-tests -d username=alice \
  --data-urlencode "password=$ALICE_PASSWORD" | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')
curl -s -X POST http://localhost:8001/api/v1/shops \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name": "Jouets des années 80"}'
```

Détails : [`deploy/compose/README.md`](deploy/compose/README.md) (pile) et [`tests/acceptance/README.md`](tests/acceptance/README.md) (tests).
