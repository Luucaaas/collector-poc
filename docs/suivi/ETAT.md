# État du projet

> Fichier maintenu **uniquement par le chef** (session principale). C'est le point d'entrée de toute reprise après interruption : voir la section « Reprise après interruption » de `CLAUDE.md`.

## Phase en cours

**Phase 10 terminée le 12/11/2026** (soutenance) pour la part du chef et des agents : README et guide du jury (P10-01), démo de 6 min outillée (P10-02), support de 20 min et diaporama de 23 diapositives (P10-03, https://claude.ai/artifact/MdhpZcHvTz1qiuib1BMHoU, privé), 68 questions probables et glossaire de 79 termes (P10-04), protocole 5 rejoué le 11/11. **Restent à Lucas** : vidéo de secours, 2 ou 3 répétitions minutées, réponse à « avez-vous réalisé ce POC seul, avec quels outils ? », relecture des références juridiques « à confirmer » et des montants des échelles d'impact, acceptation des risques résiduels R-01, R-30 et R-34, cluster reconstruit la veille (liste « La veille » de `docs/07-soutenance/demo/script-demo.md`).

Phase 9 terminée le 11/11/2026 : audit, corrections (`sha-1be69a1`), 62 risques, plan de 58 actions.

Phase 8 terminée le 06/11/2026 : charge, disponibilité et 5 indicateurs mesurés, cluster en `sha-20e080b`.

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
| P9-01 | Audit dynamique (ZAP) et rapports de scans | developpeur | `phase-9/audit-zap` | fusionnée |
| P9-02 | Corrections prioritaires du POC (dont L19) | developpeur | `phase-9/corrections` | fusionnée |
| P9-03 | Analyse de risques STRIDE et OWASP (POC et SI) | developpeur | `phase-9/analyse-risques` | fusionnée |
| P9-04 | Plan de remédiation priorisé | developpeur | `phase-9/plan-remediation` | fusionnée |
| P10-01 | README complet et guide du jury | developpeur | `phase-10/readme-guide` | fusionnée |
| P10-02 | Démo de 6 min outillée | developpeur | `phase-10/demo` | fusionnée |
| P10-03 | Contenu du support et diaporama | developpeur, chef | `phase-10/support` | fusionnée (diaporama terminé par le chef) |
| P10-04 | Questions probables et glossaire | developpeur | `phase-10/questions` | fusionnée |

Statuts possibles : à faire / en cours / en audit / fusionnée.

## Prochaine action exacte

Aucune tâche d'agent en cours. Préparation de la soutenance par Lucas (liste ci-dessus). La veille de la soutenance : suivre la liste « La veille » de `docs/07-soutenance/demo/script-demo.md` (cluster neuf, `deploy.sh all <tag>`, données de démo, `preparer.sh --veille 3` jusqu'à « PRÊT ») ; 15 minutes avant, pousser le commit vide prévu par le script. Le cluster actuel (`sha-5975ca0`) contient des données du protocole 5 (catégorie « Charge … ») : ne pas l'utiliser tel quel pour la démo.

## Décisions en attente

| Sujet | Qui décide | Remarque |
| --- | --- | --- |
| Acceptation du cluster local k3d pour le critère 5 | Lucas (question à l'intervenant) | Sinon migration vers Oracle OKE Always Free |
| Réponse à « avez-vous réalisé ce POC seul, avec quels outils ? » | Lucas | Le chef ne la rédige pas : question d'honnêteté personnelle, à préparer avant les répétitions |
| Ancien cache npm `~/.npm-ancien` (fichiers de root) | Lucas (mot de passe) | Non bloquant, à supprimer avec `sudo` quand il veut. Node 22 et `check-tools.sh --cluster` faits le 04/11/2026 |

## Dernière mise à jour

12/11/2026 13:38 — P10-04 fusionnée (`cff5795`) après un aller-retour d'audit ; documents d'architecture alignés sur le code (`9144f03`) ; protocole 5 rejoué et support mis à jour (`cfc22f8`) ; diaporama terminé ; **phase 10 terminée** pour la part du chef.
