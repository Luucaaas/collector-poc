# État du projet

> Fichier maintenu **uniquement par le chef** (session principale). C'est le point d'entrée de toute reprise après interruption : voir la section « Reprise après interruption » de `CLAUDE.md`.

## Phase en cours

**Phase 3** : expérimentations en bac à sable (`docs/04-experimentations`, critère 1). Découpage validé par Lucas le 02/11/2026 : 4 tâches (l'option Kafka est écartée), réalisées une par une dans l'ordre du tableau. Infrastructure installée depuis les images officielles par des manifestes simples, sans opérateur ni cert-manager (décision de Lucas du 03/11/2026, journal des décisions) ; kube-prometheus-stack conservé. L'expérimentation 1, faite avec l'opérateur RabbitMQ, est refaite en P3-06.

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
| P3-03 | Exp. 2 : Keycloak, Traefik et TLS mkcert | developpeur | `phase-3/exp-keycloak-tls` | en cours (brief révisé : sans opérateur) |
| P3-06 | Exp. 1 refaite sans opérateur ni cert-manager | developpeur | `phase-3/exp-rabbitmq-simple` | à faire |
| P3-05 | Synthèse, ADR 0008 et cohérence de fin de phase | developpeur | `phase-3/synthese` | à faire |

Statuts possibles : à faire / en cours / en audit / fusionnée.

## Prochaine action exacte

Demander au développeur de reprendre P3-03 avec le brief révisé (PostgreSQL et Keycloak par leurs images officielles, retrait de CloudNativePG et de Keycloak Operator), sur la branche `phase-3/exp-keycloak-tls`. Puis P3-06, puis P3-05.

## Décisions en attente

| Sujet | Qui décide | Remarque |
| --- | --- | --- |
| Acceptation du cluster local k3d pour le critère 5 | Lucas (question à l'intervenant) | Sinon migration vers Oracle OKE Always Free |
| Disque virtuel de Docker Desktop trop petit (58,4 Go) : P3-03 consomme plus de 4,5 Go et la phase 6 déploiera toute la pile. 47,7 Go occupés, dont environ 30 Go de volumes des clusters kind et 13 Go d'images des autres projets ; collector-poc en utilise environ 1 Go. Options : agrandir (plafond, fichier creux, 70 à 100 Go) ou supprimer les clusters kind devenus inutiles | Lucas (réglage de Docker Desktop) | Sans réponse. P3-03 est retentée avec 7,7 Go libres après la simplification ; arrêt si le disque passe sous 3,5 Go |
| **À relancer à la fin de P3-06** (dernière tâche qui crée un cluster) : 7 conteneurs kind d'autres projets de Lucas, arrêtés par le chef avec son accord le 02/11/2026 13:49 : `docker start projet-control-plane projet-worker projet-worker2 tp-affinity-control-plane tp-affinity-worker tp-affinity-worker2 tp-k8s-control-plane` | Chef (accord de Lucas) | Ne pas les supprimer. `mkcert -install` fait le 02/11/2026. Restent Node 22 (recommandé) et `check-tools.sh --cluster` |
| Cache npm : `sudo chown -R 501:20 ~/.npm` | Lucas (mot de passe) | Non bloquant : contourné par `npm_config_cache` pour l'export des diagrammes |

## Dernière mise à jour

03/11/2026 13:38 — Lucas valide la simplification : plus d'opérateur ni de cert-manager ; P3-03 rebriefée, P3-06 ajoutée.
