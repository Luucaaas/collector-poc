# État du projet

> Fichier maintenu **uniquement par le chef** (session principale). C'est le point d'entrée de toute reprise après interruption : voir la section « Reprise après interruption » de `CLAUDE.md`.

## Phase en cours

**Phase 6 terminée le 06/11/2026** (5 tâches P6-01 à P6-05, toutes fusionnées après audit ; contre-vérification du chef depuis un cluster neuf). Le POC tourne sur le cluster k3d local en HTTPS, déployé par `deploy/local/deploy.sh all <tag>`. Prochaine phase : **phase 7** (front React), à découper par le chef et à faire valider par Lucas.

Phase 5 terminée le 05/11/2026. Phase 4 terminée le 04/11/2026. Phase 3 terminée le 03/11/2026.

## Tâches

Identifiant : `P<phase>-<numéro>` (ex. `P2-01`). Branche : `phase-<N>/<nom-tache>`. Fiche : `docs/suivi/taches/<id>.md`.

| Id | Titre | Agent | Branche | Statut |
| --- | --- | --- | --- | --- |
| P2-01 | Indicateurs qualité | developpeur | `phase-2/indicateurs` | fusionnée |
| P2-02 | Cycle DevSecOps | developpeur | `phase-2/devsecops` | fusionnée |
| P2-03 | Schéma CI/CD détaillé | developpeur | `phase-2/schema-cicd` | fusionnée |
| P2-04 | Processus de test | developpeur | `phase-2/processus-test` | fusionnée |
| P2-05 | Matrice de compétences et recrutements | developpeur | `phase-2/matrice-competences` | fusionnée |
| P2-06 | Plan d'une action de formation | developpeur | `phase-2/plan-formation` | fusionnée |
| P2-07 | Index et cohérence de fin de phase | developpeur | `phase-2/coherence` | fusionnée |
| P3-01 | Exp. 1 : RabbitMQ sur k3d | developpeur | `phase-3/exp-rabbitmq` | fusionnée |
| P3-02 | Exp. 3 : observabilité (kube-prometheus-stack) | developpeur | `phase-3/exp-observabilite` | fusionnée |
| P3-03 | Exp. 2 : Keycloak, Traefik et TLS mkcert | developpeur | `phase-3/exp-keycloak-tls` | fusionnée |
| P3-06 | Exp. 1 refaite sans opérateur ni cert-manager | developpeur | `phase-3/exp-rabbitmq-simple` | fusionnée |
| P3-05 | Synthèse, ADR 0008 et cohérence de fin de phase | developpeur | `phase-3/synthese` | fusionnée |
| P4-01 | Socle de catalog-service | developpeur | `phase-4/socle-catalog` | fusionnée |
| P4-02 | Catégories et boutiques (US-01, US-02) | developpeur | `phase-4/categories-boutiques` | fusionnée |
| P4-03 | Articles, prix et événements (US-03, US-04) | developpeur | `phase-4/articles-prix` | fusionnée |
| P4-04 | notification-service (US-05) | developpeur | `phase-4/notification` | fusionnée |
| P4-05 | Pile docker compose et 17 tests d'acceptation | developpeur | `phase-4/acceptance` | fusionnée |
| P5-01 | Workflow backend : déclencheurs, `lint` et `test` | developpeur | `phase-5/ci-lint-test` | fusionnée |
| P5-02 | Jobs `build-scan` et `acceptance`, épinglage des images | developpeur | `phase-5/ci-build-acceptance` | fusionnée |
| P5-03 | Job `publish` : images multi-architecture sur GHCR | developpeur | `phase-5/ci-publish` | fusionnée |
| P5-04 | Job `sonar` : SonarCloud, un projet par service | developpeur | `phase-5/ci-sonar` | fusionnée |
| P5-05 | Conformité pipeline / schéma, preuves et mesures | developpeur | `phase-5/conformite` | fusionnée |
| P5-06 | Corriger les constats SonarCloud de `main` | developpeur | `phase-5/sonar-constats` | fusionnée |
| P6-01 | Cluster k3d et HTTPS | developpeur | `phase-6/cluster-tls` | fusionnée |
| P6-02 | Infrastructure : PostgreSQL, RabbitMQ, Keycloak | developpeur | `phase-6/infra` | fusionnée |
| P6-03 | Chart Helm des services et déploiement par tag | developpeur | `phase-6/chart` | fusionnée |
| P6-04 | Observabilité : Prometheus, Grafana, tableau de bord | developpeur | `phase-6/observabilite` | fusionnée |
| P6-05 | Preuves du déploiement et documentation | developpeur | `phase-6/preuves` | fusionnée |

Statuts possibles : à faire / en cours / en audit / fusionnée.

## Prochaine action exacte

Attendre que Lucas demande la phase 7, puis présenter son découpage en tâches (agent, branche, critères de fin) avant toute délégation. Acquis : cluster `collector` en place (`deploy.sh all sha-bec38ed`), client public `collector-web` du realm avec redirection `https://app.127.0.0.1.sslip.io/*`, routes `https://api.127.0.0.1.sslip.io/catalog` et `/notification`, CORS des services sur `https://app.`. Reportés : capture Grafana (phase 8, Lucas), crash brutal du broker et rotation des clés Keycloak (à planifier).

## Décisions en attente

| Sujet | Qui décide | Remarque |
| --- | --- | --- |
| Acceptation du cluster local k3d pour le critère 5 | Lucas (question à l'intervenant) | Sinon migration vers Oracle OKE Always Free |
| Ancien cache npm `~/.npm-ancien` (fichiers de root) | Lucas (mot de passe) | Non bloquant, à supprimer avec `sudo` quand il veut. Node 22 et `check-tools.sh --cluster` faits le 04/11/2026 |

## Dernière mise à jour

06/11/2026 01:07 — Phase 6 close : P6-05 fusionnée, mots de passe du cluster régénérés, contre-vérification depuis rien (212 s, `smoke.sh` 8/8, événement 0 → 1, 4 cibles `up`). `CLAUDE.md` mis à jour.
