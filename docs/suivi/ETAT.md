# État du projet

> Fichier maintenu **uniquement par le chef** (session principale). C'est le point d'entrée de toute reprise après interruption : voir la section « Reprise après interruption » de `CLAUDE.md`.

## Phase en cours

**Phase 3** : expérimentations en bac à sable (`docs/04-experimentations`, critère 1). Pas encore découpée en tâches.

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

Statuts possibles : à faire / en cours / en audit / fusionnée.

## Prochaine action exacte

Découper la phase 3 du plan de réalisation en tâches (une par expérimentation : RabbitMQ sur k3d, Keycloak + Traefik + TLS mkcert, kube-prometheus-stack), présenter le découpage à Lucas, puis, après sa validation, créer la fiche `P3-01`, l'inscrire ici et la confier au développeur.

## Décisions en attente

| Sujet | Qui décide | Remarque |
| --- | --- | --- |
| Acceptation du cluster local k3d pour le critère 5 | Lucas (question à l'intervenant) | Sinon migration vers Oracle OKE Always Free |
| Fin de la phase 0 : `mkcert -install`, Docker Desktop (8 Go, 4 CPU), Node 22, `check-tools.sh --cluster` | Lucas (mot de passe, réglages locaux) | **Bloquant pour la phase 3** (les expérimentations tournent sur k3d avec un certificat mkcert) |
| Cache npm : `sudo chown -R 501:20 ~/.npm` | Lucas (mot de passe) | Non bloquant : contourné par `npm_config_cache` pour l'export des diagrammes |

## Dernière mise à jour

31/10/2026 22:29 — P2-07 fusionnée (audit n° 2 conforme, contre-vérification du chef : 48 liens valides, export des 13 diagrammes sans erreur). Phase 2 terminée.
