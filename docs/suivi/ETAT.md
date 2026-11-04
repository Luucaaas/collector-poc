# État du projet

> Fichier maintenu **uniquement par le chef** (session principale). C'est le point d'entrée de toute reprise après interruption : voir la section « Reprise après interruption » de `CLAUDE.md`.

## Phase en cours

**Phase 5 en cours** (pipeline CI/CD, contrat `docs/01-qualite/cicd.md`), lancée le 04/11/2026 à la demande de Lucas. 5 tâches, faites l'une après l'autre car elles modifient toutes `backend.yml`. Les branches de la phase 5 sont poussées sur GitHub pour obtenir de vraies exécutions.

Phase 4 terminée le 04/11/2026 (5 tâches fusionnées après audit, 17/17 tests d'acceptation). Phase 3 terminée le 03/11/2026 (5 tâches fusionnées après audit).

Phases précédentes : phase 0 (outillage, reste des actions de Lucas), phase 1 terminée et refondue pour le POC simplifié (ADR 0007), **phase 2 terminée le 31/10/2026** (7 tâches ci-dessous, toutes fusionnées après audit conforme).

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
| P5-04 | Job `sonar` : SonarCloud, un projet par service | developpeur | `phase-5/ci-sonar` | à faire (attend Lucas) |
| P5-05 | Conformité pipeline / schéma, preuves et mesures | developpeur | `phase-5/conformite` | fusionnée |

Statuts possibles : à faire / en cours / en audit / fusionnée.

## Prochaine action exacte

Seule P5-04 reste, bloquée par Lucas : vérifier les deux projets SonarCloud (`Luucaaas_collector-poc_catalog-service`, `Luucaaas_collector-poc_notification-service`, API publique `search_projects?organization=luucaaas`) et le secret `SONAR_TOKEN` (`gh secret list`). Dès qu'ils existent : confier P5-04 au développeur (branche `phase-5/ci-sonar` depuis `main`, livrée par pull request), audit, fusion de la PR, relevé du run de `main`, puis clôture de la phase 5 (contre-vérification, `CLAUDE.md`, bilan à Lucas).

## Décisions en attente

| Sujet | Qui décide | Remarque |
| --- | --- | --- |
| Acceptation du cluster local k3d pour le critère 5 | Lucas (question à l'intervenant) | Sinon migration vers Oracle OKE Always Free |
| SonarCloud : 2 projets (`Luucaaas_collector-poc_catalog-service`, `Luucaaas_collector-poc_notification-service`), analyse automatique désactivée, secret GitHub `SONAR_TOKEN` | Lucas (compte externe) | Demandé le 04/11/2026, bloque P5-04 seulement |
| Ancien cache npm `~/.npm-ancien` (fichiers de root) | Lucas (mot de passe) | Non bloquant, à supprimer avec `sudo` quand il veut. Node 22 et `check-tools.sh --cluster` faits le 04/11/2026 |

## Dernière mise à jour

04/11/2026 13:21 — P5-05 fusionnée (corrections du chef). P5-04 attend les projets SonarCloud et le secret `SONAR_TOKEN` de Lucas.
