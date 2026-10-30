# CLAUDE.md — collector-poc

Contexte et décisions du projet, à lire avant toute tâche.

## Le projet

POC de **Collector.shop** (vente d'objets de collection entre particuliers, commission de 5 %), pour l'évaluation individuelle du bloc CESI MAALSI « Superviser et assurer le développement des applications logicielles ». Lucas y joue le rôle de **Lead Developer**.

- **Objectif : la note A**, soit une moyenne ≥ 4,6/5 sur les 10 critères de la grille. On peut avoir au plus 4 critères à 4, tous les autres doivent être à 5.
- **Soutenance** : 20 min de présentation + 15 min d'échange, avec démo du POC et vidéo de secours. Le jury est technique : vocabulaire précis exigé.
- **Fichiers du sujet** (sur le Mac, hors repo) : `~/Desktop/Cesi/BLOC S3/` (consignes, contexte Collector, grille d'évaluation .xlsx). Les relire en cas de doute sur une exigence.
- **Plan de réalisation détaillé** (phases et cases à cocher) : https://claude.ai/artifact/EZGZuZEMD6xP9v2mftk9fk

## Ce que la grille exige (points de vigilance)

| Critère | Ce qu'il faut pour 5/5 |
| --- | --- |
| 1. Protocole d'expérimentation | Vrai protocole reproductible (environnement + versions, étapes, résultats mesurés, difficultés, limites, décision). Pas un guide d'installation |
| 2. Qualité du POC | Valide découpage, communication interservice, sécurité, hébergement/orchestration. Documenté (README exécutable) |
| 3. Fonctionnalité métier | Répond au besoin du contexte Collector |
| 4. CI/CD | Processus schématisé ET pipeline réel conforme au schéma |
| 5. Environnement d'exécution | « Environnement managé » + disponibilité et montée en charge démontrées |
| 6. Indicateurs qualité | ≥ 4 indicateurs, réellement mesurés, avec axes d'amélioration contre la dette technique |
| 7. Tests | Processus formalisé + au moins 2 types de tests appliqués, qui passent |
| 8. Sécurité | Plan de remédiation priorisé (tout le SI) + au moins 2 bonnes pratiques dans le POC |
| 9. Compétences | Matrice de compétences + action de formation détaillée |
| 10. Présentation | Schémas lisibles, démo préparée, discours fluide |

## Fonctionnalité métier du POC

Un vendeur publie un article ou modifie son prix → **contrôle automatique** (champs, prix > 0, aucun email ni téléphone dans le texte) → article `PUBLISHED` ou `REJECTED` → événements RabbitMQ → les acheteurs intéressés sont notifiés et le service anti-fraude analyse l'événement.

User stories :
1. Admin : créer une catégorie
2. Vendeur : créer une boutique
3. Vendeur : publier un article (contrôle automatique)
4. Vendeur : modifier le prix d'un article (historique conservé)
5. Acheteur : définir ses centres d'intérêt et préférences, recevoir les notifications
6. Admin : consulter les alertes de fraude

Hors périmètre (architecture cible seulement) : paiement, chat, notation, recommandations, publicité, enchères.

## Architecture et stack (décisions prises)

| Brique | Choix |
| --- | --- |
| Backend | Python 3.12, **FastAPI**, Pydantic v2, SQLAlchemy 2.0, Alembic, aio-pika, PyJWT, structlog, prometheus-fastapi-instrumentator, uv |
| Services | `catalog-service`, `notification-service`, `fraud-service` (une base PostgreSQL par service) |
| Événements | RabbitMQ, exchange `article.events` : `article.published`, `article.price_changed`. Consommateurs idempotents |
| Front | **React + TypeScript** (Vite), MUI, React Router, TanStack Query, React Hook Form + Zod, react-i18next, react-oidc-context (PKCE, token en mémoire) |
| Auth | **Keycloak** (realm `collector`, rôles `buyer`, `seller`, `admin`). Les rôles sont vérifiés côté API |
| Tests | pytest, pytest-cov, testcontainers-python, pytest-bdd (acceptation), Locust (charge), Vitest, Playwright |
| Qualité / sécurité | Ruff, mypy, Bandit, Semgrep, pip-audit, Gitleaks, Trivy, OWASP ZAP, SonarCloud |
| CI/CD | GitHub Actions, images sur GHCR (`ghcr.io/luucaaas/<service>`, multi-arch amd64 + arm64) |
| Hébergement | **Tout en local sur le Mac** : Kubernetes **k3d** (1 server + 2 agents), Helm, ingress-nginx, cert-manager (CA locale via mkcert, domaines `*.127.0.0.1.sslip.io`), **Argo CD** en GitOps |
| Observabilité | kube-prometheus-stack (Prometheus + Grafana) |

Choix écartés (à justifier dans les ADR) : Kafka (surdimensionné pour la V1), Django (trop monolithique), front HTMX/Jinja et Streamlit (Lucas veut une techno classique), cloud avec crédits d'essai (l'infra doit être 100 % gratuite).

**Migration cloud** : uniquement si l'intervenant refuse le cluster local pour le critère 5. Cible : Oracle OKE Always Free, avec les mêmes charts Helm.

## Organisation du repo

```
docs/01-qualite          indicateurs ISO 25010, DevSecOps, schéma CI/CD, processus de test
docs/02-architecture     schémas cible et POC, adr/
docs/03-backlog          exigences, user stories, critères d'acceptation
docs/04-experimentations un protocole par technologie testée
docs/05-competences      matrice de compétences, plan de formation
docs/06-securite         rapports de scans, STRIDE / OWASP, plan de remédiation
services/<nom>-service   un service FastAPI par dossier (src/, tests/, Dockerfile, pyproject.toml)
frontend/                application React
tests/acceptance         tests d'acceptation pytest-bdd
tests/load               scénarios Locust et résultats
deploy/local             scripts du cluster k3d
deploy/infra             values Helm de l'infrastructure
deploy/helm              chart des services
deploy/k8s               manifests (NetworkPolicies, ClusterIssuer, applications Argo CD)
.github/workflows        pipelines
```

## Conventions

- Documentation, README et messages de commit **en français**. Code et identifiants en anglais.
- Chaque service expose `/health/live`, `/health/ready` et `/metrics`, et écrit des logs JSON avec un identifiant de corrélation.
- Écrire les tests en même temps que le code. Pas de fonctionnalité sans test.
- Aucun secret dans le repo : `.env.example` versionné, `.env` ignoré. Secrets Kubernetes pour le cluster.
- Images Docker multi-stage, utilisateur non-root, base `python:3.12-slim`.
- Tout ce qui sert au jury doit être reproductible par script (cluster, expérimentations, tests de charge).

## Travailler avec Lucas

- Il maîtrise surtout **Python**. React/TypeScript, Kubernetes, Helm et GitHub Actions sont nouveaux pour lui : explique les choix et les commandes, car il devra les défendre à l'oral.
- Il est sur **macOS**. Les commandes qui demandent son mot de passe (Homebrew, `mkcert -install`) et les réglages de Docker Desktop sont à faire par lui.
- Avancement : phase 0 en cours. Repo créé, comptes SonarCloud et GHCR prêts. Restent l'installation des outils et la question à poser à l'intervenant sur le cluster local (critère 5).
