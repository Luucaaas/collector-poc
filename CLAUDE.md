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
| CI/CD | GitHub Actions, contrat dans `docs/01-qualite/cicd.md`. `backend.yml` en matrice : `lint` (Ruff, mypy) → `test` (pytest, couverture ≥ 80 %) → `sonar` → `build-scan` (image amd64, Trivy bloquant) → `acceptance` (`docker compose`) → `publish` sur `main` (Buildx + QEMU, amd64 + arm64, `ghcr.io/luucaaas/<service>:sha-<commit>`). `frontend.yml` : job `frontend` (ESLint → Vitest → `npm audit --omit=dev --audit-level=high` → image nginx non root amd64 → Trivy bloquant) → `publish` sur `main` (index amd64 + arm64 poussé par digest sans tag, Trivy sur ce digest pour les deux architectures, puis tags `sha-<7>` et `main`, garde-fou tag = digest scanné). Les deux workflows tournent à chaque push : un commit de `main` donne les trois images au même tag. Déploiement manuel par `deploy.sh services <tag>` |
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
- Limites assumées L1 à L25 dans `architecture-poc.md` section 8 : elles alimentent le plan de remédiation (critère 8).
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
  - **Phase 0** : repo, comptes SonarCloud et GHCR, script `deploy/local/check-tools.sh`, Python 3.12 (uv). `mkcert -install` fait (02/11/2026) ; Docker Desktop réservé au projet (autres projets supprimés par Lucas le 03/11/2026, environ 53 Go libres). Le 04/11/2026 : `check-tools.sh --cluster` réussi (3 nœuds Ready), Docker Desktop à 10 CPU et 8 Go, Node 22.23.4 installé par Homebrew (prioritaire sur l'ancien Node 20 de `/usr/local/bin`), cache npm détenu par root renommé en `~/.npm-ancien` (à supprimer par Lucas avec `sudo` quand il veut). Reste la question à l'intervenant sur le cluster local (critère 5).
  - **Phase 1 terminée** (30/10/2026), puis **refondue pour le POC simplifié** (31/10/2026) : `docs/03-backlog` (36 EF, 31 ENF, 9 RM, 5 stories pour 17 points et 17 critères), `docs/02-architecture` (cible complète, POC simplifié avec limites L1 à L16, contrats des 2 services, SVG, ADR 0001 à 0007). Plus de fichiers `.feature`.
  - **Phase 2 terminée** (31/10/2026), réalisée par l'organisation multi-agents (7 tâches, suivi dans `docs/suivi`) : `docs/01-qualite` (5 indicateurs I1 à I5 reliés à l'ISO 25010 et aux ENF, cycle DevSecOps en 8 étapes, schéma CI/CD qui sert de contrat à la phase 5, processus de test avec RACI) et `docs/05-competences` (matrice de 26 compétences, 3 recrutements, plan de formation Kubernetes et Helm de 28 h). Rôle de Product Owner tenu par un·e dirigeant·e.
  - **Phase 3 terminée** (03/11/2026), 5 tâches (P3-01, P3-02, P3-03, P3-05, P3-06) : trois protocoles reproductibles dans `docs/04-experimentations` (RabbitMQ, Keycloak + Traefik + TLS mkcert, observabilité), chacun avec `run.sh` et journal d'exécution versionné, puis ADR 0008. Essai des opérateurs abandonné pour la simplicité (broker de nouveau prêt en 10 s au lieu de 54 s, 64 Mi de moins). Limites L17 à L20 ajoutées.
  - **Phase 4 terminée** (04/11/2026), 5 tâches (P4-01 à P4-05) : `catalog-service` (270 tests, couverture 99 %) et `notification-service` (186 tests, 98 %), socle recopié d'un service à l'autre (`auth.py` identique), événements RabbitMQ publiés après le commit et consommés en lecteur tolérant. Pile locale `deploy/compose/` (`up.sh`, `down.sh --volumes`, mots de passe générés dans `deploy/compose/.env`), 17 tests d'acceptation dans `tests/acceptance` (17/17 après un démarrage à froid). Realm de base dans `deploy/keycloak/` (sans client de test). Limites L21 et L22 ajoutées.
  - **Phase 5 terminée** (05/11/2026), 6 tâches (P5-01 à P5-06, P5-04 et P5-06 livrées par pull request) : `.github/workflows/backend.yml` conforme au contrat `cicd.md` (`lint` → `test` → `sonar` → `build-scan` → `acceptance` → `publish`), preuves dans `docs/01-qualite/conformite-pipeline.md`, mesures d'I1, I2, I4 et I5 dans `indicateurs.md`. Choix à défendre : actions épinglées par SHA, `ubuntu-24.04`, `persist-credentials: false`, images épinglées par digest, Trivy 0.76.0 en binaire vérifié par SHA-256 (compromission de `trivy-action` en mars 2026), `sonar` seulement sur `main` et les pull requests (plan gratuit de SonarCloud), pas d'annulation des runs sur `main`. Images publiques `ghcr.io/luucaaas/<service>:sha-<7>` (amd64 + arm64). SonarCloud : 2 projets, 0 constat après correction de S8414 (CORS) et S8786 (expression régulière quadratique : 24 s → 2 ms sur 100 000 caractères). Branches de tâche poussées sur GitHub pendant la phase, puis supprimées.
  - **Phase 6 terminée** (06/11/2026), 5 tâches (P6-01 à P6-05) : `deploy/local/cluster.sh create | verify | delete` (k3d 1 server + 2 agents, k3s épinglé, HTTPS mkcert, redirection 301/308), `deploy/local/deploy.sh infra | monitoring | services <tag> | all <tag>` (mots de passe générés dans `deploy/local/.env`, Secrets par fichier et `--server-side`, images `tag@digest` vérifiées sur GHCR avant tout changement, migrations par Job Helm, réplicas laissés à l'HPA, `smoke.sh`, `helm rollback` automatique), `deploy/infra` (PostgreSQL en lecture seule, RabbitMQ, Keycloak sur `https://auth.`), chart `deploy/helm/collector-service`, kube-prometheus-stack 91.9.0 épinglé (Grafana sur `https://grafana.`, tableau de bord par service). Protocole 4 (`docs/04-experimentations/04-deploiement`) : déploiement depuis rien en 199 s, auto-réparation en 7,1 s sans requête perdue, retour arrière d'une version défaillante sans requête perdue, traçabilité pod → digest → commit → run de CI. Seuil de disque : 10 000 Mo. Limites L17 mise à jour et L23 ajoutée (le retour arrière ne défait pas les migrations). Capture du tableau de bord Grafana reportée en phase 8 (Lucas, navigateur ; mot de passe `GRAFANA_ADMIN_PASSWORD` de `deploy/local/.env`).
  - **Phase 7 terminée** (06/11/2026), 5 tâches (P7-01 à P7-05) : front `frontend/` (Vite, React 19, TypeScript strict, MUI, React Router, react-oidc-context ; versions exactes publiées depuis au moins 14 jours), connexion PKCE S256 avec jetons en mémoire (`userStore` `InMemoryWebStorage`, état de redirection en `sessionStorage`), configuration lue sur `/config.json`, 4 pages, 62 tests Vitest, 6 parcours Playwright (`frontend/e2e/run-compose.sh` et `run-cluster.sh`, mots de passe lus dans les `.env`, contrôle des violations de CSP dans le navigateur), captures pour la soutenance dans `frontend/e2e/resultats/captures/`. Image nginx non root (uid 101, `apk upgrade` car la base officielle était vulnérable : L25), en-têtes de sécurité, CSP par modèle `envsubst` (`style-src 'unsafe-inline'` imposé par Emotion : L24). `frontend.yml` décrit ci-dessus (preuves dans `conformite-pipeline.md` §6). Chart générique étendu au front (`deploy/helm/values/frontend.yaml`, Ingress `app.` en mode `root`), `smoke.sh` à 18 contrôles, `deploy.sh realm` (recrée la base `keycloak` pour réimporter le realm : à lancer seulement avec l'accord de Lucas). Realm : scope `profile` minimal (`preferred_username`), redirection après déconnexion, page de connexion en français ; `localhost:5173` seulement dans le realm de la pile compose. Contre-vérification depuis un cluster neuf en `sha-cd5751f` : 214 s, `smoke.sh` 18/18, Playwright 6/6 ; la recréation de la base de Keycloak a aussi prouvé la rotation des clés (rechargement JWKS sur `kid` inconnu).
  - **Phase 8 terminée** (06/11/2026), 4 tâches (P8-01 à P8-04) : métrique `notification_delay_seconds` (ENF-14) et son panneau Grafana ; `tests/load/` (Locust 2.47.0, connexion par le vrai flux PKCE, 80 % de lecteurs et 20 % de vendeurs, `run.sh` qui produit `resume.md`) : à 50 utilisateurs, p95 21 ms en lecture et 23 ms en publication, 0 réponse 5xx, délai des notifications sous 0,1 s ; protocole 5 `docs/04-experimentations/05-charge-disponibilite/` : pic de 200 utilisateurs, HPA de 2 à 5 réplicas en 60 s, pod supprimé en pleine charge remplacé en 4,9 s sans erreur (533 requêtes), retour à 2 en 325 s, 0 réponse 5xx sur 20 235, captures Grafana prises par script (mot de passe lu dans `.env`, jamais vu par un agent) ; relevé des 5 indicateurs sur une même version dans `indicateurs.md` avec la dette chiffrée (lignes et branches non couvertes, 15 erreurs `mypy` dans les tests, 531 lignes de socle dupliquées entre services, bundle de 609 Ko) et des axes d'amélioration. Grafana limité à 768 Mi (il était tué à 384 Mi). Copies de conflit iCloud « nom 2 » retirées (dont une ancienne version de `frontend.yml` qui publiait en double) et ignorées par `.gitignore` : le dossier du projet est sur le Bureau synchronisé par iCloud. Contre-vérification depuis un cluster neuf en `sha-20e080b` : 213 s, `smoke.sh` 18/18, Playwright 6/6, mot de passe de Grafana régénéré.
  - Prochaine étape : phase 9 (audit de sécurité : ZAP, STRIDE, OWASP, plan de remédiation priorisé sur tout le SI).
