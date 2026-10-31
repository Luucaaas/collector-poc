# État du projet

> Fichier maintenu **uniquement par le chef** (session principale). C'est le point d'entrée de toute reprise après interruption : voir la section « Reprise après interruption » de `CLAUDE.md`.

## Phase en cours

**Phase 2** : processus qualité et compétences (`docs/01-qualite`, `docs/05-competences`). Pas encore découpée en tâches.

Phases précédentes : phase 0 (outillage, reste des actions de Lucas), phase 1 terminée et refondue pour le POC simplifié (ADR 0007).

## Tâches

Identifiant : `P<phase>-<numéro>` (ex. `P2-01`). Branche : `phase-<N>/<nom-tache>`. Fiche : `docs/suivi/taches/<id>.md`.

| Id | Titre | Agent | Branche | Statut |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Statuts possibles : à faire / en cours / en audit / fusionnée.

## Prochaine action exacte

Découper la phase 2 du plan de réalisation en tâches courtes, créer la fiche `docs/suivi/taches/P2-01.md` avec son brief, l'inscrire dans ce tableau, commiter les deux sur main, puis la confier à l'agent `developpeur`.

## Décisions en attente

| Sujet | Qui décide | Remarque |
| --- | --- | --- |
| Acceptation du cluster local k3d pour le critère 5 | Lucas (question à l'intervenant) | Sinon migration vers Oracle OKE Always Free |
| Fin de la phase 0 : `mkcert -install`, Docker Desktop (8 Go, 4 CPU), Node 22, `check-tools.sh --cluster` | Lucas (mot de passe, réglages locaux) | Bloquant pour la phase de déploiement, pas pour la phase 2 |

## Dernière mise à jour

31/10/2026 21:00 — mise en place de l'organisation multi-agents.
