# État du projet

> Fichier maintenu **uniquement par le chef** (session principale). C'est le point d'entrée de toute reprise après interruption : voir la section « Reprise après interruption » de `CLAUDE.md`.

## Phase en cours

**Phase 8 terminée le 06/11/2026** (4 tâches P8-01 à P8-04, toutes fusionnées après audit ; contre-vérification du chef depuis un cluster neuf en `sha-20e080b`). I3 et ENF-14 mesurés et conformes, montée en charge et disponibilité démontrées (protocole 5), 5 indicateurs relevés avec la dette chiffrée. Prochaine phase : **phase 9** (audit de sécurité et plan de remédiation), à découper par le chef et à faire valider par Lucas.

Phase 7 terminée le 06/11/2026 : front React sur le cluster en HTTPS, tout au tag `sha-cd5751f`.

Phase 6 terminée le 06/11/2026. Phase 5 terminée le 05/11/2026. Phase 4 terminée le 04/11/2026. Phase 3 terminée le 03/11/2026.

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
| P7-01 | Socle du front et connexion | developpeur | `phase-7/socle-front` | fusionnée |
| P7-02 | Pages métier, tests Vitest et parcours Playwright | developpeur | `phase-7/pages` | fusionnée |
| P7-03 | Image nginx et `frontend.yml` | developpeur | `phase-7/ci-front` | fusionnée |
| P7-04 | Déploiement du front sur le cluster | developpeur | `phase-7/deploiement-front` | fusionnée |
| P7-05 | Parcours Playwright sur le cluster et preuves | developpeur | `phase-7/e2e` | fusionnée |
| P8-01 | Délai des notifications mesuré (ENF-14) | developpeur | `phase-8/delai-notifications` | fusionnée |
| P8-02 | Scénarios Locust | developpeur | `phase-8/locust` | fusionnée |
| P8-03 | Protocole 5 : charge et disponibilité | developpeur | `phase-8/charge-disponibilite` | fusionnée |
| P8-04 | Relevé des indicateurs et axes d'amélioration | developpeur | `phase-8/indicateurs` | fusionnée |

Statuts possibles : à faire / en cours / en audit / fusionnée.

## Prochaine action exacte

Attendre que Lucas demande la phase 9, puis présenter son découpage en tâches (agent, branche, critères de fin) avant toute délégation. Acquis : cluster neuf en `sha-20e080b`, mot de passe de Grafana régénéré. À reprendre en phase 9 : L1 à L25 (`architecture-poc.md` §8), L19 (console d'administration de Keycloak publique), axes de sécurité d'`indicateurs.md` (Trivy local et vulnérabilités sans correctif, arm64 des services non scanné, `npm audit fix` majeur), panne brutale du broker (sans outbox).

## Décisions en attente

| Sujet | Qui décide | Remarque |
| --- | --- | --- |
| Acceptation du cluster local k3d pour le critère 5 | Lucas (question à l'intervenant) | Sinon migration vers Oracle OKE Always Free |
| Ancien cache npm `~/.npm-ancien` (fichiers de root) | Lucas (mot de passe) | Non bloquant, à supprimer avec `sudo` quand il veut. Node 22 et `check-tools.sh --cluster` faits le 04/11/2026 |

## Dernière mise à jour

06/11/2026 14:18 — Phase 8 close : P8-04 fusionnée (`20e080b`), contre-vérification depuis un cluster neuf (213 s, `smoke.sh` 18/18, Playwright 6/6), plan de réalisation et `CLAUDE.md` mis à jour.
