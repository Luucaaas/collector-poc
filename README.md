# Collector.shop — POC

[![backend](https://github.com/Luucaaas/collector-poc/actions/workflows/backend.yml/badge.svg?branch=main)](https://github.com/Luucaaas/collector-poc/actions/workflows/backend.yml)
[![frontend](https://github.com/Luucaaas/collector-poc/actions/workflows/frontend.yml/badge.svg?branch=main)](https://github.com/Luucaaas/collector-poc/actions/workflows/frontend.yml)

Pipeline CI/CD : schéma et contrat dans [docs/01-qualite/cicd.md](docs/01-qualite/cicd.md), preuves de conformité et mesures dans [docs/01-qualite/conformite-pipeline.md](docs/01-qualite/conformite-pipeline.md). Le lien vers les projets SonarCloud sera ajouté avec la tâche P5-04.

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
| Plateforme | Docker, Kubernetes local (k3d), Traefik, Helm (déploiement par script `deploy/local/deploy.sh`) |
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

Pile `docker compose` : PostgreSQL, RabbitMQ, Keycloak (realm `collector`) et les deux services. Elle sert aux tests d'acceptation et à la CI. Le déploiement sur Kubernetes est décrit plus bas, dans « Déployer sur le cluster local ».

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

Front React (`npm run dev` sur `http://localhost:5173`, contre cette pile) : voir [`frontend/README.md`](frontend/README.md).

## Déployer sur le cluster local

Cluster Kubernetes **k3d** (1 server + 2 agents) sur le Mac, avec Traefik, HTTPS par un certificat mkcert, PostgreSQL, RabbitMQ, Keycloak, Prometheus et Grafana, puis les deux services du POC et le front (2 réplicas chacun, HPA de 2 à 5). Tout se fait par scripts de `deploy/local/` ; la preuve chronométrée est dans [le compte rendu du déploiement](docs/04-experimentations/04-deploiement/protocole.md).

**Prérequis** (macOS). Les outils sont vérifiés par `deploy/local/check-tools.sh` ; la mémoire et les CPU de Docker Desktop sont des réglages à faire soi-même ; le disque libre et les ports 80 et 443 sont contrôlés par `deploy/local/cluster.sh create` :

- Docker Desktop démarré, avec 10 CPU et 8 Go de mémoire (configuration mesurée) et au moins 10 Go de disque libres dans la machine virtuelle de Docker (`cluster.sh create` s'arrête sinon) ;
- ports 80 et 443 du Mac libres ;
- Homebrew, git, k3d, kubectl, helm, mkcert, uv avec Python 3.12, Node 22 (`brew install k3d kubectl helm mkcert uv node@22` ; `uv python install 3.12`) ;
- **déjà fait, une seule fois** : `mkcert -install` (installe l'autorité de certification dans le Mac, demande votre mot de passe : à faire vous-même, aucun script ne le lance).

Toutes les commandes se lancent **depuis la racine du dépôt**.

```bash
deploy/local/check-tools.sh                  # vérifie les outils et leurs versions
deploy/local/cluster.sh create               # cluster k3d + certificat + HTTPS (environ 1 min)
deploy/local/deploy.sh all sha-cd5751f       # infrastructure, supervision, services et front, puis test de fumée (environ 2 min 30)
```

`sha-cd5751f` est le tag d'une image publiée par la CI (le tag `sha-<7 premiers caractères du commit>` d'un run `publish` réussi de GitHub Actions). `deploy.sh` vérifie que l'image existe sur GHCR avant de modifier quoi que ce soit, génère les mots de passe manquants dans `deploy/local/.env` (ignoré par Git, jamais affiché), déploie par `helm upgrade --install`, lance `smoke.sh` et revient en arrière (`helm rollback`) si une étape échoue. Il est relançable sans erreur.

| Quoi | Où |
| --- | --- |
| API du catalogue | https://api.127.0.0.1.sslip.io/catalog/api/v1/categories |
| API des notifications | https://api.127.0.0.1.sslip.io/notification/api/v1/me/notifications (jeton requis : 401 sans) |
| Application web (front) | https://app.127.0.0.1.sslip.io |
| Keycloak | https://auth.127.0.0.1.sslip.io/realms/collector |
| Grafana | https://grafana.127.0.0.1.sslip.io (utilisateur `admin`, mot de passe `GRAFANA_ADMIN_PASSWORD` dans `deploy/local/.env`) |

L'application web (React, dossier `frontend/`, servie par nginx) utilise ces URL ; si le realm a changé sur un cluster existant, `deploy/local/deploy.sh realm` l'applique ([détails](deploy/README.md)) ; l'API peut aussi se tester directement par elles (le realm du cluster ne contient pas le client de test de la pile `docker compose`).

```bash
curl -s https://api.127.0.0.1.sslip.io/catalog/api/v1/categories     # 200, liste (vide au départ)
deploy/local/smoke.sh                                                 # contrôles par l'Ingress (services et front), HTTPS vérifié sans -k
deploy/local/publish-test-event.sh                                    # publie un événement sur RabbitMQ et vérifie qu'il est consommé
kubectl --context k3d-collector -n collector get pods -o wide         # placement des pods sur les 3 nœuds
helm --kube-context k3d-collector -n collector history catalog-service # révisions Helm (retour arrière possible)
deploy/local/cluster.sh delete                                        # supprime le cluster (garde le certificat et le .env)
```

### Utiliser l'application

Ouvrir https://app.127.0.0.1.sslip.io (le certificat mkcert est reconnu après `mkcert -install`). Le catalogue est public ; « Connexion » redirige vers Keycloak (`https://auth.127.0.0.1.sslip.io`, page en français).

| Compte | Rôles | Pages utiles |
| --- | --- | --- |
| `admin` | `admin` | Catégories |
| `alice` | `seller`, `buyer` | Vendre, Mes centres d'intérêt |
| `bob` | `seller` | Vendre |
| `chloe` | `buyer` | Mes centres d'intérêt et notifications |

Les mots de passe sont dans `deploy/local/.env` (jamais versionné), aux clés `ADMIN_PASSWORD`, `ALICE_PASSWORD`, `BOB_PASSWORD` et `CHLOE_PASSWORD`. Preuve que le parcours complet fonctionne sur le cluster (navigateur réel, HTTPS vérifié) : [journal d'exécution Playwright](frontend/e2e/resultats/journal-cluster.txt) et [captures d'écran](frontend/e2e/resultats/captures/). Pour le rejouer : `frontend/e2e/run-cluster.sh` (voir [`frontend/README.md`](frontend/README.md)).

Détails, mesures et limites : [`deploy/README.md`](deploy/README.md) (scripts, chart, retour arrière, observabilité) et [`docs/04-experimentations/04-deploiement/protocole.md`](docs/04-experimentations/04-deploiement/protocole.md) (déroulé chronométré, mémoire, auto-réparation, retour arrière, traçabilité).
