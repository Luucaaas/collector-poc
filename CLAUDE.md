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
| Tests | pytest, pytest-cov, testcontainers-python, tests d'acceptation pytest + httpx (environ 15, nommés d'après les critères), Locust (charge), Vitest, Playwright |
| Qualité / sécurité | CI : Ruff, mypy, SonarCloud, Trivy. OWASP ZAP lancé ponctuellement pour l'audit de sécurité |
| CI/CD | GitHub Actions : Ruff + mypy → pytest + couverture → SonarCloud → build Docker multi-arch → Trivy → push GHCR (`ghcr.io/luucaaas/<service>`, amd64 + arm64) |
| Hébergement | **Tout en local sur le Mac** : Kubernetes **k3d** (1 server + 2 agents, aucune règle de placement), **Traefik** fourni par k3s (ingress-nginx écarté car retiré par Kubernetes), certificat `*.127.0.0.1.sslip.io` généré par **mkcert** et chargé comme Secret TLS. Un **chart Helm générique** pour les 2 services (2 réplicas, sondes, HPA, ressources, secrets), déployé par `deploy/local/deploy.sh` (`helm upgrade --install`) |
| Observabilité | kube-prometheus-stack allégé (sans Alertmanager), un tableau de bord Grafana (débit, latence p95, taux d'erreur), logs JSON corrélés |

Décisions (détail dans `docs/02-architecture/contrats.md`, `architecture-poc.md` et les ADR 0001 à 0007) :

- **Aucun appel HTTP entre services** : les événements transportent l'état utile (catégorie, vendeur, titre, prix).
- Contrôle automatique synchrone : non conforme → `REJECTED` (201, motifs `CONTACT_EMAIL`, `CONTACT_PHONE`) ; requête mal formée → 422. Prix modifié par `PUT /articles/{id}/price` (idempotent).
- Boutique avec coordonnées → 422 (`CONTACT_EMAIL`, `CONTACT_PHONE`). Boutique ou catégorie inexistante dans le corps → 422 (`SHOP_NOT_FOUND`, `CATEGORY_NOT_FOUND`).
- Doublons de notification évités par `UNIQUE (user_id, source_event_id)` et `ON CONFLICT DO NOTHING`. Pas de table `processed_events`.
- Montants en chaîne décimale (`"120.00"`), erreurs au format RFC 9457, routes `/api/v1`. Hôtes : `app.`, `api.` (`/catalog`, `/notification`), `auth.`, `grafana.127.0.0.1.sslip.io`. `X-Request-ID` généré par les services.
- Les services récupèrent les clés JWKS par l'URL interne de Keycloak, mais vérifient `iss` avec l'URL publique. L'audience `collector-api` est ajoutée par un mapper « Audience ».
- La sonde `/health/ready` ne teste que PostgreSQL, jamais RabbitMQ.
- Jetons OIDC en mémoire (`userStore` configuré, sinon `sessionStorage` par défaut). BFF dans la cible.
- Démo de disponibilité : suppression d'un pod et scaling HPA (2 → 5 réplicas) pendant un test Locust. Pas de démo de panne de nœud.
- Limites assumées L1 à L16 dans `architecture-poc.md` section 8 : elles alimentent le plan de remédiation (critère 8).
- Cible (dans `architecture-cible.md`) : fraud-service, outbox, quorum queues et DLQ, NetworkPolicies, PostgreSQL par service et répliqué, Argo CD, cert-manager, PDB et répartition imposée, mTLS, BFF, statut `PENDING_REVIEW` et service moderation.
- Diagrammes : Mermaid dans les `.md`, export SVG par `docs/02-architecture/export-diagrams.sh` (mermaid-cli 11.17.0, car la 12 exige Node 22).

Choix écartés (justifiés dans les ADR) : Kafka (surdimensionné pour la V1), Django (trop monolithique), front HTMX/Jinja et Streamlit (Lucas veut une techno classique), cloud avec crédits d'essai (l'infra doit être 100 % gratuite), Argo CD, cert-manager et Gherkin pour le POC (ADR 0006 et 0007).

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
deploy/infra             values Helm de l'infrastructure
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
  - **Phase 0** : repo, comptes SonarCloud et GHCR, script `deploy/local/check-tools.sh`, Python 3.12 (uv). Restent `mkcert -install`, Docker Desktop (8 Go, 4 CPU), Node 22 recommandé, `check-tools.sh --cluster`, et la question à l'intervenant sur le cluster local (critère 5).
  - **Phase 1 terminée** (30/10/2026), puis **refondue pour le POC simplifié** (31/10/2026) : `docs/03-backlog` (36 EF, 31 ENF, 9 RM, 5 stories pour 17 points et 17 critères), `docs/02-architecture` (cible complète, POC simplifié avec limites L1 à L16, contrats des 2 services, SVG, ADR 0001 à 0007). Plus de fichiers `.feature`.
  - Prochaine étape : phase 2 (processus qualité, compétences).
