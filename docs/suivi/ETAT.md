# État du projet

> Fichier maintenu **uniquement par le chef** (session principale). C'est le point d'entrée de toute reprise après interruption : voir la section « Reprise après interruption » de `CLAUDE.md`.

## Phase en cours

**Phase 4** : backend (`catalog-service`, `notification-service`, `docker compose`, tests). Découpage validé par Lucas le 03/11/2026 : 5 tâches réalisées une par une dans l'ordre du tableau. Livrable : les 5 user stories fonctionnent en local avec `docker compose`, tous les tests passent.

Phase 3 terminée le 03/11/2026 (5 tâches fusionnées après audit).

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
| P4-02 | Catégories et boutiques (US-01, US-02) | developpeur | `phase-4/categories-boutiques` | en cours (corrections de l'audit n° 1) |
| P4-03 | Articles, prix et événements (US-03, US-04) | developpeur | `phase-4/articles-prix` | à faire |
| P4-04 | notification-service (US-05) | developpeur | `phase-4/notification` | à faire |
| P4-05 | Pile docker compose et 17 tests d'acceptation | developpeur | `phase-4/acceptance` | à faire |

Statuts possibles : à faire / en cours / en audit / fusionnée.

## Prochaine action exacte

Attendre les corrections du développeur sur P4-02 (aller-retour n° 1), puis audit n° 2 et fusion.

## Décisions en attente

| Sujet | Qui décide | Remarque |
| --- | --- | --- |
| Acceptation du cluster local k3d pour le critère 5 | Lucas (question à l'intervenant) | Sinon migration vers Oracle OKE Always Free |
| Outillage restant de Lucas | Lucas | `mkcert -install` fait le 02/11/2026. Restent Node 22 (recommandé) et `check-tools.sh --cluster` |
| Cache npm : `sudo chown -R 501:20 ~/.npm` | Lucas (mot de passe) | Non bloquant : contourné par `npm_config_cache` pour l'export des diagrammes |

## Dernière mise à jour

03/11/2026 20:49 — P4-02 : audit n° 1 non conforme (500 sur un slug long, pagination, contrôle des coordonnées), renvoyée au développeur.
