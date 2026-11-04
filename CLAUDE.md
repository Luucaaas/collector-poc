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

POC **simplifié au strict minimum qui garde la note A** (ADR 0007, 31/10/2026). Un vendeur publie un article ou modifie son prix → **contrôle automatique** (champs, prix > 0, aucun email ni téléphone dans le texte) → article `PUBLISHED` ou `REJECTED` → événement RabbitMQ → les acheteurs intéressés (par la catégorie) sont notifiés. L'outil anti-fraude est un **point d'extension** : il s'abonnera à l'exchange `article.events` sans modifier `catalog-service`.

User stories (5, 17 points, 17 critères d'acceptation) :
1. Admin : créer une catégorie
2. Vendeur : créer une boutique
3. Vendeur : publier un article (contrôle automatique)
4. Vendeur : modifier le prix d'un article (historique conservé)
5. Acheteur : définir ses centres d'intérêt et préférences, recevoir les notifications

Hors périmètre (architecture cible seulement) : détection de fraude (ancienne US-06), paiement, chat, notation, recommandations, publicité, enchères, i18n, contrôle d'accessibilité.

## Architecture et stack (décisions prises)

| Brique | Choix |
| --- | --- |
| Backend | Python 3.12, **FastAPI**, Pydantic v2, SQLAlchemy 2.0, Alembic, aio-pika, PyJWT, structlog, prometheus-fastapi-instrumentator, uv |
| Services | `catalog-service` (catégories, boutiques, articles, contrôle, historique des prix) et `notification-service` (centres d'intérêt, préférences, notifications) |
| Données | **1 instance PostgreSQL** : bases logiques `catalog_db`, `notification_db` et base de Keycloak, un utilisateur PostgreSQL par service |
| Événements | RabbitMQ, exchange `topic` `article.events` (`article.published`, `article.price_changed`), une file durable `notification.article-events`. Publication juste après le commit, sans outbox |
| Front | **React + TypeScript** (Vite), MUI, React Router, react-oidc-context (PKCE, jetons en mémoire). 4 pages : catalogue, mise en vente et prix, centres d'intérêt et notifications, catégories (admin). En français |
| Auth | **Keycloak**, realm `collector` importé depuis un JSON, rôles `buyer`, `seller`, `admin`, comptes `admin`, `alice`, `bob`, `chloe`. Les rôles sont vérifiés côté API |
| Tests | pytest, pytest-cov, testcontainers-python, tests d'acceptation pytest + httpx (un par critère, 17, sur une pile `docker compose`), Locust (charge), Vitest, Playwright (ponctuel sur le cluster, hors CI) |
| Qualité / sécurité | CI : Ruff, mypy, SonarCloud (un projet par service), Trivy (`--scanners vuln,secret`), ESLint pour le front. OWASP ZAP lancé ponctuellement pour l'audit de sécurité |
| CI/CD | GitHub Actions, contrat dans `docs/01-qualite/cicd.md`. `backend.yml` en matrice : `lint` (Ruff, mypy) → `test` (pytest, couverture ≥ 80 %) → `sonar` → `build-scan` (image amd64, Trivy bloquant) → `acceptance` (`docker compose`) → `publish` sur `main` (Buildx + QEMU, amd64 + arm64, `ghcr.io/luucaaas/<service>:sha-<commit>`). `frontend.yml` (phase 7) : ESLint → Vitest → build → image nginx non-root → Trivy → GHCR. Déploiement manuel par `deploy.sh <tag>` |
| Hébergement | **Tout en local sur le Mac** : Kubernetes **k3d** (1 server + 2 agents, aucune règle de placement), **Traefik** fourni par k3s (ingress-nginx écarté car retiré par Kubernetes), certificat `*.127.0.0.1.sslip.io` généré par **mkcert** et chargé comme Secret TLS. Un **chart Helm générique** pour les 2 services (2 réplicas, sondes, HPA, ressources, secrets), déployé par `deploy/local/deploy.sh` (`helm upgrade --install`). **Infrastructure** (PostgreSQL 18.4, RabbitMQ 4.3.5, Keycloak 26.8.0) depuis les **images officielles par des manifestes simples** (StatefulSet, Deployment, Services), **sans opérateur, sans CRD ajoutée, sans cert-manager** (ADR 0008). Un seul namespace `collector` |
| Observabilité | kube-prometheus-stack allégé, seule exception par chart Helm et opérateur (ADR 0008) : Prometheus, opérateur, Grafana, kube-state-metrics et kubelet gardés ; Alertmanager, node-exporter, plan de contrôle, règles et tableaux de bord par défaut désactivés. Bornes d'histogramme alignées sur les seuils d'I3 (300 et 500 ms) ; un tableau de bord Grafana (débit, latence p95, taux d'erreur), logs JSON corrélés |

Décisions (détail dans `docs/02-architecture/contrats.md`, `architecture-poc.md` et les ADR 0001 à 0008) :

- **Aucun appel HTTP entre services** : les événements transportent l'état utile (catégorie, vendeur, titre, prix).
- Contrôle automatique synchrone : non conforme → `REJECTED` (201, motifs `CONTACT_EMAIL`, `CONTACT_PHONE`) ; requête mal formée → 422. Prix modifié par `PUT /articles/{id}/price` (idempotent).
- Boutique avec coordonnées → 422 (`CONTACT_EMAIL`, `CONTACT_PHONE`). Boutique ou catégorie inexistante dans le corps → 422 (`SHOP_NOT_FOUND`, `CATEGORY_NOT_FOUND`).
- Doublons de notification évités par `UNIQUE (user_id, source_event_id)` et `ON CONFLICT DO NOTHING`. Pas de table `processed_events`.
- Montants en chaîne décimale (`"120.00"`), erreurs au format RFC 9457, routes `/api/v1`. Hôtes : `app.`, `api.` (`/catalog`, `/notification`), `auth.`, `grafana.127.0.0.1.sslip.io`. `X-Request-ID` repris s'il fait au plus 128 caractères de `[A-Za-z0-9._-]`, sinon généré par le service ; champ de log `correlation_id`.
- Les services récupèrent les clés JWKS par l'URL interne de Keycloak (`http://keycloak.collector.svc.cluster.local:8080`), en cache, mais vérifient `iss` avec l'URL publique (`https://auth.127.0.0.1.sslip.io/realms/collector`). RS256 imposé, titre unique pour tous les 401, raison du rejet seulement dans les logs. L'audience `collector-api` est ajoutée par un mapper « Audience ».
- La sonde `/health/ready` ne teste que PostgreSQL, jamais RabbitMQ.
- Jetons OIDC en mémoire (`userStore` configuré, sinon `sessionStorage` par défaut). BFF dans la cible.
- Démo de disponibilité : suppression d'un pod et scaling HPA (2 → 5 réplicas) pendant un test Locust. Pas de démo de panne de nœud.
- Secrets : `deploy.sh` génère les mots de passe manquants dans un `.env` local non versionné (modèle `.env.example`, à créer en phase 6), puis crée les Secrets Kubernetes. Un utilisateur PostgreSQL par service, sans droit de superutilisateur.
- Ce que la phase 3 impose aux phases 4 et 6 : section « Synthèse et conséquences pour le POC » de `docs/04-experimentations/README.md`.
- Limites assumées L1 à L22 dans `architecture-poc.md` section 8 : elles alimentent le plan de remédiation (critère 8).
- Cible (dans `architecture-cible.md`) : fraud-service, outbox, quorum queues et DLQ, NetworkPolicies, PostgreSQL par service et répliqué, Argo CD, cert-manager, PDB et répartition imposée, mTLS, BFF, statut `PENDING_REVIEW` et service moderation.
- Diagrammes : Mermaid dans les `.md` de `docs/02-architecture` et `docs/01-qualite`, export SVG par `docs/02-architecture/export-diagrams.sh` (mermaid-cli 11.17.0, car la 12 exige Node 22). Le rendu n'est pas déterministe : ne jamais commiter un SVG régénéré dont la source n'a pas changé (`git checkout --` après l'export). Vérifier la lisibilité d'un nouveau schéma en PNG (`qlmanage -t -s 1600`).

Choix écartés (justifiés dans les ADR) : Kafka (surdimensionné pour la V1), Django (trop monolithique), front HTMX/Jinja et Streamlit (Lucas veut une techno classique), cloud avec crédits d'essai (l'infra doit être 100 % gratuite), Argo CD, cert-manager et Gherkin pour le POC (ADR 0006 et 0007), charts Bitnami et opérateurs (RabbitMQ Cluster Operator, CloudNativePG, Keycloak Operator) pour le POC (ADR 0008, opérateurs dans la cible).

**Migration cloud** : uniquement si l'intervenant refuse le cluster local pour le critère 5. Cible : Oracle OKE Always Free, avec le même chart Helm.

## Organisation du repo

```
docs/01-qualite          indicateurs ISO 25010, DevSecOps, schéma CI/CD, processus de test
docs/02-architecture     schémas cible et POC, adr/
docs/03-backlog          exigences, user stories, critères d'acceptation
docs/04-experimentations un protocole par technologie testée
docs/05-competences      matrice de compétences, plan de formation
docs/06-securite         rapports de scans, STRIDE / OWASP, plan de remédiation
docs/suivi               ETAT.md, fiches de tâche (taches/), journal des décisions
.claude/agents           agents developpeur et auditeur
services/<nom>-service   un service FastAPI par dossier (src/, tests/, Dockerfile, pyproject.toml)
frontend/                application React
tests/acceptance         tests d'acceptation pytest + httpx
tests/load               scénarios Locust et résultats
deploy/local             scripts du cluster k3d (check-tools.sh, deploy.sh)
deploy/infra             manifestes de PostgreSQL, RabbitMQ, Keycloak et values de kube-prometheus-stack
deploy/helm              chart générique des services
deploy/k8s               manifests complémentaires (Secret TLS mkcert, Ingress)
.github/workflows        pipelines
```

## Conventions

- Documentation, README et messages de commit **en français**. Code et identifiants en anglais.
- Chaque service expose `/health/live`, `/health/ready` et `/metrics`, et écrit des logs JSON avec un identifiant de corrélation.
- Écrire les tests en même temps que le code. Pas de fonctionnalité sans test.
- Aucun secret dans le repo : `.env.example` versionné, `.env` ignoré. Secrets Kubernetes pour le cluster.
- Images Docker multi-stage, utilisateur non-root, base `python:3.12-slim`.
- Tout ce qui sert au jury doit être reproductible par script (cluster, expérimentations, tests de charge).

## Organisation multi-agents

Trois rôles :

| Rôle | Qui | Modèle | Ce qu'il fait |
| --- | --- | --- | --- |
| Chef | La session principale | Opus | Découpe, délègue, arbitre, fusionne, tient le suivi |
| Développeur | Agent `developpeur` (`.claude/agents/developpeur.md`) | Sonnet | Réalise une tâche sur sa branche, tient le journal de la fiche |
| Auditeur | Agent `auditeur` (`.claude/agents/auditeur.md`) | Haiku | Vérifie une branche sans rien modifier, rend un verdict |

Le suivi vit dans `docs/suivi/` : `ETAT.md` (tenu uniquement par le chef), une fiche par tâche dans `taches/<id>.md` (modèle dans `taches/README.md`) et `journal-decisions.md`.

Le chef :

- Découpe chaque phase du plan en tâches courtes, avec des critères de fin vérifiables.
- Avant chaque délégation : crée la fiche de tâche avec le brief, met à jour `ETAT.md`, puis commite les deux sur main.
- Confie chaque tâche au développeur, sur une branche `phase-N/nom-tache`.
- Après chaque tâche, lance l'auditeur sur la branche et recopie son rapport dans la fiche.
- Si le verdict est NON CONFORME : renvoie les écarts au développeur (2 allers-retours maximum, puis il tranche lui-même).
- Si l'auditeur remonte un DOUTE, ou si le développeur pose une question : tranche et consigne la décision dans `docs/suivi/journal-decisions.md`.
- Fusionne sur main et pousse uniquement quand l'audit est CONFORME. Pour les tâches critiques (sécurité, fin de phase), refait lui-même une contre-vérification finale.
- Après chaque résultat, met à jour `ETAT.md` et le commite.
- Ne sollicite Lucas que pour : un changement de périmètre, une action qui demande son mot de passe ou un compte externe, ou une décision irréversible.
- À la fin de chaque phase : met à jour l'avancement dans ce fichier et fait un bilan court à Lucas.
- Horodate `ETAT.md`, les fiches et le journal avec `date "+%d/%m/%Y %H:%M"`, jamais au jugé.

Si les agents `developpeur` et `auditeur` ne sont pas chargés (session ouverte avant leur création), le chef utilise l'agent généraliste avec le modèle du fichier d'agent (Sonnet ou Haiku) et le texte de ce fichier comme consigne ; l'auditeur reçoit en plus l'interdiction d'écrire et de changer de branche (lecture par `git show` et `git diff`).

### Reprise après interruption

Après une coupure (limite d'usage, session fermée) :

1. Lire `docs/suivi/ETAT.md`.
2. Lire la fiche de la tâche en cours (`docs/suivi/taches/<id>.md`), en particulier le journal et « Reste à faire ».
3. Vérifier l'état réel avec git : branche de la tâche (`git branch -a`), derniers commits (`git log --oneline -5 <branche>`), modifications non commitées (`git status`), puis relancer les tests, `ruff check` et `mypy` si du code est concerné.
4. Si l'état réel diffère de `ETAT.md`, corriger `ETAT.md` d'abord.
5. Exécuter la « Prochaine action exacte » d'`ETAT.md`.

## Travailler avec Lucas

- Il maîtrise surtout **Python**. React/TypeScript, Kubernetes, Helm et GitHub Actions sont nouveaux pour lui : explique les choix et les commandes, car il devra les défendre à l'oral.
- Il est sur **macOS**. Les commandes qui demandent son mot de passe (Homebrew, `mkcert -install`) et les réglages de Docker Desktop sont à faire par lui.
- Avancement :
  - **Phase 0** : repo, comptes SonarCloud et GHCR, script `deploy/local/check-tools.sh`, Python 3.12 (uv). `mkcert -install` fait (02/11/2026) ; Docker Desktop réservé au projet (autres projets supprimés par Lucas le 03/11/2026, environ 53 Go libres). Restent Docker Desktop (8 Go, 4 CPU) à vérifier, Node 22 recommandé, `check-tools.sh --cluster`, et la question à l'intervenant sur le cluster local (critère 5).
  - **Phase 1 terminée** (30/10/2026), puis **refondue pour le POC simplifié** (31/10/2026) : `docs/03-backlog` (36 EF, 31 ENF, 9 RM, 5 stories pour 17 points et 17 critères), `docs/02-architecture` (cible complète, POC simplifié avec limites L1 à L16, contrats des 2 services, SVG, ADR 0001 à 0007). Plus de fichiers `.feature`.
  - **Phase 2 terminée** (31/10/2026), réalisée par l'organisation multi-agents (7 tâches, suivi dans `docs/suivi`) : `docs/01-qualite` (5 indicateurs I1 à I5 reliés à l'ISO 25010 et aux ENF, cycle DevSecOps en 8 étapes, schéma CI/CD qui sert de contrat à la phase 5, processus de test avec RACI) et `docs/05-competences` (matrice de 26 compétences, 3 recrutements, plan de formation Kubernetes et Helm de 28 h). Rôle de Product Owner tenu par un·e dirigeant·e.
  - Poste de Lucas : le cache `~/.npm` contient des fichiers appartenant à root. Correctif à lancer par lui : `sudo chown -R 501:20 ~/.npm`. En attendant, l'export des diagrammes passe par `npm_config_cache=<dossier temporaire>`.
  - **Phase 3 terminée** (03/11/2026), 5 tâches (P3-01, P3-02, P3-03, P3-05, P3-06) : trois protocoles reproductibles dans `docs/04-experimentations` (RabbitMQ, Keycloak + Traefik + TLS mkcert, observabilité), chacun avec `run.sh` et journal d'exécution versionné, puis ADR 0008. Essai des opérateurs abandonné pour la simplicité (broker de nouveau prêt en 10 s au lieu de 54 s, 64 Mi de moins). Limites L17 à L20 ajoutées.
  - **Phase 4 terminée** (04/11/2026), 5 tâches (P4-01 à P4-05) : `catalog-service` (270 tests, couverture 99 %) et `notification-service` (186 tests, 98 %), socle recopié d'un service à l'autre (`auth.py` identique), événements RabbitMQ publiés après le commit et consommés en lecteur tolérant. Pile locale `deploy/compose/` (`up.sh`, `down.sh --volumes`, mots de passe générés dans `deploy/compose/.env`), 17 tests d'acceptation dans `tests/acceptance` (17/17 après un démarrage à froid). Realm de base dans `deploy/keycloak/` (sans client de test). Limites L21 et L22 ajoutées.
  - Prochaine étape : phase 5 (pipeline CI/CD, contrat `docs/01-qualite/cicd.md`).
