# État du projet

> Fichier maintenu **uniquement par le chef** (session principale). C'est le point d'entrée de toute reprise après interruption : voir la section « Reprise après interruption » de `CLAUDE.md`.

## Phase en cours

**Phase 2** : processus qualité et compétences (`docs/01-qualite`, `docs/05-competences`). Découpage validé par Lucas le 31/10/2026 : 7 tâches, réalisées une par une dans l'ordre du tableau.

Phases précédentes : phase 0 (outillage, reste des actions de Lucas), phase 1 terminée et refondue pour le POC simplifié (ADR 0007).

## Tâches

Identifiant : `P<phase>-<numéro>` (ex. `P2-01`). Branche : `phase-<N>/<nom-tache>`. Fiche : `docs/suivi/taches/<id>.md`.

| Id | Titre | Agent | Branche | Statut |
| --- | --- | --- | --- | --- |
| P2-01 | Indicateurs qualité | developpeur | `phase-2/indicateurs` | en cours (aller-retour n° 1) |
| P2-02 | Cycle DevSecOps | developpeur | `phase-2/devsecops` | à faire |
| P2-03 | Schéma CI/CD détaillé | developpeur | `phase-2/schema-cicd` | à faire |
| P2-04 | Processus de test | developpeur | `phase-2/processus-test` | à faire |
| P2-05 | Matrice de compétences et recrutements | developpeur | `phase-2/matrice-competences` | à faire |
| P2-06 | Plan d'une action de formation | developpeur | `phase-2/plan-formation` | à faire |
| P2-07 | Index et cohérence de fin de phase | developpeur | `phase-2/coherence` | à faire |

Statuts possibles : à faire / en cours / en audit / fusionnée.

## Prochaine action exacte

Renvoyer au développeur les écarts de l'audit n° 1 de P2-01 (fiche, section « Suite donnée par le chef »), puis relancer l'auditeur.

## Décisions en attente

| Sujet | Qui décide | Remarque |
| --- | --- | --- |
| Acceptation du cluster local k3d pour le critère 5 | Lucas (question à l'intervenant) | Sinon migration vers Oracle OKE Always Free |
| Fin de la phase 0 : `mkcert -install`, Docker Desktop (8 Go, 4 CPU), Node 22, `check-tools.sh --cluster` | Lucas (mot de passe, réglages locaux) | Bloquant pour la phase de déploiement, pas pour la phase 2 |

## Dernière mise à jour

31/10/2026 21:40 — P2-01 : audit n° 1 non conforme, renvoyée au développeur (aller-retour n° 1).
