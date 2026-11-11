# Guide du jury

Ce guide répond à une question : **pour chacun des 10 critères de la grille, où est le livrable et où est la preuve ?** Chaque ligne renvoie vers un document, un script ou un résultat du dépôt. Chaque chiffre vient d'un fichier du dépôt, cité à côté ; le script [`verifier-guide.py`](verifier-guide.py) contrôle que les liens existent et que les chiffres cités se retrouvent dans leur fichier source.

- Le POC se lance par les commandes du [README](../../README.md) : cluster neuf et application en HTTPS en moins de 5 minutes.
- La grille est à la racine du dépôt : [`Grille_eval_bloc_INFMAALSIA2V_Superviser_dev_apps_logicielles.xlsx`](../../Grille_eval_bloc_INFMAALSIA2V_Superviser_dev_apps_logicielles.xlsx).
- Les mesures de qualité sont relevées sur une même version du code (relevé du 06/11/2026, commit `22364bc`). L'audit de sécurité et le plan de remédiation datent du 10 et du 11/11/2026, après corrections (commit `1be69a1`).

## Vue d'ensemble

| # | Critère | Livrable principal | Preuve la plus parlante |
| --- | --- | --- | --- |
| 1 | Protocole d'expérimentation | [5 protocoles reproductibles](../04-experimentations/README.md) | 0 message perdu sur 2 × 1 000, broker prêt en 10 s, déploiement à froid en 199 s |
| 2 | Qualité du POC | [Architecture du POC](../02-architecture/architecture-poc.md), [README exécutable](../../README.md) | README suivi tel quel sur un cluster neuf : déploiement en 174 s, 6 parcours sur 6 |
| 3 | Fonctionnalité métier | [5 user stories](../03-backlog/user-stories.md) | 17 critères d'acceptation sur 17, 6 parcours Playwright sur 6 |
| 4 | CI/CD | [Schéma](../01-qualite/cicd.md) et [conformité du pipeline](../01-qualite/conformite-pipeline.md) | Run `backend` de 11 jobs verts, blocages démontrés par des runs rouges |
| 5 | Environnement d'exécution | [Protocole 5](../04-experimentations/05-charge-disponibilite/protocole.md) | HPA de 2 à 5 réplicas en 60 s, pod remplacé en 4,9 s sans erreur |
| 6 | Indicateurs qualité | [5 indicateurs mesurés](../01-qualite/indicateurs.md) | Couverture 98,45 % et 97,66 %, 0 réponse 5xx, dette chiffrée et axes d'amélioration |
| 7 | Processus de test | [Processus de test](../01-qualite/processus-test.md) | Tests unitaires, d'intégration, d'acceptation, de composants, de bout en bout, de charge et de sécurité, tous verts |
| 8 | Sécurité | [Plan de remédiation](../06-securite/plan-remediation.md) | 62 risques, 58 actions, 17 bonnes pratiques prouvées dans le POC |
| 9 | Compétences | [Matrice](../05-competences/matrice.md) et [plan de formation](../05-competences/plan-formation.md) | 26 compétences, 3 recrutements, formation de 28 heures |
| 10 | Présentation | [Schémas du dépôt](#10-qualité-de-la-présentation) et démonstration par le README | 14 schémas SVG, 7 captures d'écran du parcours complet |

## 1. Fiabilité du protocole d'expérimentation

**Pour 5/5** : un protocole présenté, avec technologies, interactions, difficultés et résultats qui permettent de valider l'adoption ; reproductible, pas un guide d'installation.

| Où le trouver | Ce que c'est |
| --- | --- |
| [Index et modèle commun](../04-experimentations/README.md) | Chaque protocole suit 8 rubriques : question posée, technologies et interactions, environnement (versions exactes), étapes reproductibles (`run.sh`), résultats mesurés, difficultés, limites, décision |
| [1 RabbitMQ](../04-experimentations/01-rabbitmq/protocole.md), [2 Keycloak + TLS](../04-experimentations/02-keycloak-tls/protocole.md), [3 Observabilité](../04-experimentations/03-observabilite/protocole.md) | Les trois technologies testées en bac à sable, chacune sur un cluster jetable, avec journal d'exécution versionné dans `resultats/` |
| [4 Déploiement](../04-experimentations/04-deploiement/protocole.md), [5 Charge et disponibilité](../04-experimentations/05-charge-disponibilite/protocole.md) | Le déploiement du POC lui-même et sa montée en charge, mesurés |
| [Synthèse et conséquences pour le POC](../04-experimentations/README.md#synthèse-et-conséquences-pour-le-poc) | Ce que chaque expérience impose aux phases suivantes ; décisions reprises dans l'[ADR 0008](../02-architecture/adr/0008-infrastructure-images-officielles.md) |

**Preuves mesurées**

| Mesure | Valeur | Source |
| --- | --- | --- |
| RabbitMQ : messages perdus lors de la suppression du pod du broker | 0 message perdu sur 2 × 1 000 | [index des expérimentations](../04-experimentations/README.md) |
| RabbitMQ : retour à Ready du broker, sans opérateur contre avec | 10 s au lieu de 54 s | idem |
| Keycloak : cas d'autorisation vérifiés | 15 cas d'autorisation conformes | idem |
| Déploiement à froid du POC complet | 199 s depuis rien | idem |
| Auto-réparation : 2 réplicas de nouveau prêts après suppression d'un pod | 7,1 s | [protocole 4](../04-experimentations/04-deploiement/protocole.md) |

**Limites assumées.** Une option, Kafka, n'a pas été expérimentée : elle est écartée par l'[ADR 0003](../02-architecture/adr/0003-rabbitmq-plutot-que-kafka.md). Chaque protocole a une section « Limites de l'expérimentation » (par exemple, seul l'arrêt propre du broker est testé, pas un arrêt brutal).

## 2. Qualité technique du prototype

**Pour 5/5** : le POC valide les points clés de l'architecture (découpage, communication interservice, sécurité, hébergement, orchestration) et il est documenté.

| Point clé | Où le trouver | Ce qui le valide |
| --- | --- | --- |
| Découpage | [Architecture du POC](../02-architecture/architecture-poc.md), [contrats](../02-architecture/contrats.md), [ADR 0001](../02-architecture/adr/0001-microservices-evenements.md) | 2 services, 2 bases logiques, un utilisateur PostgreSQL par service |
| Communication interservice | [contrats](../02-architecture/contrats.md), [ADR 0003](../02-architecture/adr/0003-rabbitmq-plutot-que-kafka.md) | Événements RabbitMQ, aucun appel HTTP entre services ; démontré par les 17 critères d'acceptation et par `deploy/local/publish-test-event.sh` |
| Sécurité | [Plan de remédiation, bonnes pratiques prouvées](../06-securite/plan-remediation.md#7-déjà-appliqué-dans-le-poc) | OIDC avec PKCE, JWT validé localement, TLS, conteneurs non root, Trivy et SonarCloud bloquants |
| Hébergement et orchestration | [`deploy/README.md`](../../deploy/README.md), [chart Helm](../../deploy/helm/collector-service), [`deploy/local/`](../../deploy/local) | k3d (1 server et 2 agents), Traefik, Helm, 2 réplicas et HPA de 2 à 5 |
| Documentation exécutable | [README](../../README.md) | Suivi tel quel depuis un cluster supprimé |

**Preuves mesurées**

| Mesure | Valeur | Source |
| --- | --- | --- |
| README suivi tel quel depuis un cluster supprimé : déploiement de l'ensemble (`deploy.sh all`) | 174 s, `smoke.sh` vert, 6 parcours Playwright sur 6 | [fiche P10-01, journal](../suivi/taches/P10-01.md) |
| Mémoire des pods du déploiement complet | 1 938 Mi | [index des expérimentations](../04-experimentations/README.md) |
| Critères d'acceptation passés sur les deux services, RabbitMQ et Keycloak | 17 sur 17 | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) |

**Limites assumées.** [L1 à L25](../02-architecture/architecture-poc.md#8-limites-assumées-du-poc) (une instance PostgreSQL pour tout, certificat mkcert, plan de contrôle unique…) : chacune est justifiée et alimente le plan de remédiation.

## 3. Démonstration de fonctionnalité métier

**Pour 5/5** : la fonctionnalité développée répond aux besoins fonctionnels exprimés par la maîtrise d'ouvrage.

| Où le trouver | Ce que c'est |
| --- | --- |
| [Exigences](../03-backlog/exigences.md) | EF-01 à EF-36, ENF-01 à ENF-31, RM-01 à RM-09, avec le périmètre POC ou cible de chacune |
| [User stories](../03-backlog/user-stories.md) | 5 stories (créer une catégorie, créer une boutique, publier un article avec contrôle automatique, modifier le prix, notifier les acheteurs intéressés) |
| [Tests d'acceptation](../../tests/acceptance/README.md) | Un test pytest par critère d'acceptation |
| [Parcours Playwright](../../frontend/e2e/resultats/journal-cluster.txt) et [captures](../../frontend/e2e/resultats/captures/) | Le parcours complet dans un navigateur réel sur le cluster, en HTTPS |

**Preuves mesurées**

| Mesure | Valeur | Source |
| --- | --- | --- |
| User stories, points, critères d'acceptation | 5 stories, 17 points, 17 critères | [user stories](../03-backlog/user-stories.md) |
| Critères d'acceptation passés | 17 sur 17 en 9,84 s | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) |
| Parcours de bout en bout sur le cluster, relevé du 06/11/2026 (`sha-cd5751f`) | 6 parcours sur 6 | idem |
| Parcours de bout en bout sur un cluster neuf, relancés le 11/11/2026 (`sha-ee45469`) | 6 sur 6 en 9,6 s | [fiche P10-01, journal](../suivi/taches/P10-01.md) |

**Limites assumées.** Le POC couvre la chaîne publier, contrôler, notifier. Hors périmètre, justifiés par l'[ADR 0007](../02-architecture/adr/0007-simplification-perimetre-poc.md) : détection de fraude (point d'extension par l'exchange `article.events`), paiement, chat, notation, enchères.

## 4. Conformité du processus CI/CD

**Pour 5/5** : le processus est schématisé et conforme aux exigences ; le POC intègre la plateforme de livraison continue conformément au processus décrit.

| Où le trouver | Ce que c'est |
| --- | --- |
| [Schéma CI/CD](../01-qualite/cicd.md) | Environnements, déclencheurs, jobs de `lint` à `publish`, conditions de blocage, traçabilité par tag et digest, écarts avec la cible. Schémas : [vue d'ensemble](../01-qualite/img/pipeline-cicd.svg) et [détail du job backend](../01-qualite/img/pipeline-backend.svg) |
| [`backend.yml`](../../.github/workflows/backend.yml) et [`frontend.yml`](../../.github/workflows/frontend.yml) | Le pipeline réel, à chaque push |
| [Conformité du pipeline](../01-qualite/conformite-pipeline.md#2-tableau-de-conformité) | Pour chaque élément du schéma, la ligne du workflow et un run qui le prouve |
| [Déploiement](../../deploy/README.md) | `deploy.sh services <tag>` : image vérifiée sur GHCR avant tout changement, tag et digest, retour arrière automatique |

**Preuves mesurées**

| Mesure | Valeur | Source |
| --- | --- | --- |
| Run `backend` de référence de la phase 8 | 11 jobs verts, de `lint` à `publish` | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) (run 42219458020) |
| Run `frontend` correspondant | 2 jobs verts | idem (run 42219458005) |
| Premier run de référence : durée du pipeline | 5 min 47 s, 9 jobs verts | [conformité du pipeline](../01-qualite/conformite-pipeline.md) |
| Blocages démontrés | `lint`, `build-scan` (CVE CRITICAL) et quality gate SonarCloud en échec par des runs rouges | [conformité, preuves de blocage](../01-qualite/conformite-pipeline.md#4-preuves-de-blocage) |
| Déploiement tracé du pod au run de CI | pod, digest, commit, run | [protocole 4](../04-experimentations/04-deploiement/protocole.md) |

**Limites assumées.** Déploiement lancé à la main (pas de déploiement continu : Argo CD est dans la cible) ; un seul environnement d'exécution ; tests de charge et Playwright hors CI. Voir la section « Écarts entre le POC et la cible » de [cicd.md](../01-qualite/cicd.md).

## 5. Validation de l'environnement d'exécution

**Pour 5/5** : le POC s'exécute dans un environnement managé ; la disponibilité et la montée en charge sont démontrées.

| Où le trouver | Ce que c'est |
| --- | --- |
| [Architecture du POC, vue physique](../02-architecture/architecture-poc.md) | Cluster Kubernetes k3d (distribution k3s certifiée CNCF), 3 nœuds, Traefik, chart Helm, sondes, ressources bornées, HPA |
| [Protocole 5](../04-experimentations/05-charge-disponibilite/protocole.md), [résumé de l'exécution](../04-experimentations/05-charge-disponibilite/resultats/20261106-1132/resume.md) | Montée en charge de l'HPA et suppression d'un pod en pleine charge, avec captures Grafana |
| [Protocole 4](../04-experimentations/04-deploiement/protocole.md) | Déploiement à froid, mémoire et disque, auto-réparation, retour arrière d'une version défaillante |
| [Grafana](../../deploy/README.md) | Tableau de bord « Collector - service » (débit, p95, taux d'erreur, réplicas) sur `https://grafana.127.0.0.1.sslip.io` |

**Preuves mesurées**

| Mesure | Valeur | Source |
| --- | --- | --- |
| Montée de l'HPA sous un pic de 200 utilisateurs | 2 à 5 réplicas prêts en 60 s | [index des expérimentations](../04-experimentations/README.md) |
| Pod supprimé en pleine charge | remplacé en 4,9 s, 0 échec sur 533 requêtes | idem |
| Retour à 2 pods après la charge | 325 s | idem |
| Réponses 5xx sur l'ensemble du pic | 0 réponse 5xx sur 20 235 requêtes | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) |
| Auto-réparation sans charge | 7,1 s, sans requête perdue | [protocole 4](../04-experimentations/04-deploiement/protocole.md) |

**Limites assumées, à connaître avant la soutenance.** L'environnement est un **cluster Kubernetes local** (k3d), pas un service géré par un fournisseur : l'[ADR 0006](../02-architecture/adr/0006-kubernetes-local-k3d-argocd.md) est acceptée sous réserve de ce critère, avec un repli documenté (Oracle OKE Always Free, même chart Helm). Pas de démonstration de panne de nœud (placement non imposé, limite L8) ; le plafond de l'HPA est atteint vers 200 utilisateurs.

## 6. Pertinence et mesure des indicateurs de qualité

**Pour 5/5** : au moins 4 indicateurs servent les objectifs de qualité ; leur mesure met en évidence des axes d'amélioration contre la dette technique.

| Où le trouver | Ce que c'est |
| --- | --- |
| [Indicateurs](../01-qualite/indicateurs.md) | 5 indicateurs rattachés à l'ISO 25010 (I1 couverture, I2 dette technique, I3 latence et erreurs, I4 vulnérabilités, I5 critères d'acceptation), avec seuil, outil, moment de mesure et action |
| [Relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) | Les 5 indicateurs mesurés sur une même version, avec la source de chaque valeur |
| Axes d'amélioration | Section « Axes d'amélioration contre la dette technique » du même relevé |

**Preuves mesurées** (aucun indicateur n'est hors seuil)

| Indicateur | Mesure | Seuil | Source |
| --- | --- | --- | --- |
| I1 couverture | 98,45 % (`catalog-service`) et 97,66 % (`notification-service`) | ≥ 80 % | [indicateurs](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8), run 42219458020 |
| I2 dette technique SonarCloud | dette de 0 min, duplication de 0,0 %, note A, 0 code smell | note A, duplication < 3 % | idem |
| I3 latence | p95 de 21 ms en lecture et de 23 ms en publication, à 50 utilisateurs | < 300 ms et < 500 ms | idem ; [résultats de charge](../../tests/load/resultats/20261106-1106/resume.md) |
| I3 erreurs | 0 sur 6 564 requêtes | moins de 1 % de 5xx | idem |
| I4 vulnérabilités | 0 vulnérabilité CRITICAL ou HIGH avec correctif, 0 secret | 0 | idem |
| I5 critères d'acceptation | 17 sur 17 | 17 sur 17 | idem |

**Dette mise en évidence, avec ses actions** (même relevé) : socle recopié dans les deux services (531 lignes en double, 34,6 % des lignes de `src`, invisible pour SonarCloud, cible : paquet partagé) ; 15 erreurs de `mypy --strict` dans les dossiers de tests, qui ne sont pas contrôlés en CI ; bundle du front de 609,4 Ko ; plafond de l'HPA atteint à environ 200 utilisateurs.

**Limites assumées.** Une seule exécution de référence par scénario de charge, sur le même Mac que le cluster ; la complexité cognitive par fonction n'est mesurée que par un indice (complexité cyclomatique).

## 7. Conformité du processus de test

**Pour 5/5** : le processus de test est formalisé (types de tests, outils, sorties attendues, parties prenantes) ; au moins deux types de tests sont appliqués au POC, avec une couverture suffisante, et passent.

| Où le trouver | Ce que c'est |
| --- | --- |
| [Processus de test](../01-qualite/processus-test.md) | Pyramide, tableau des types de tests (outil, emplacement, moment, sortie attendue, responsable), correspondance avec les jobs de la CI, traçabilité, RACI, gestion des anomalies. Schéma : [pyramide des tests](../01-qualite/img/pyramide-tests.svg) |
| `services/*/tests/` | Tests unitaires, d'intégration (testcontainers), d'API et de sécurité (pytest) |
| [`tests/acceptance/`](../../tests/acceptance/README.md) | 17 tests d'acceptation, un par critère |
| [`frontend/`](../../frontend/README.md) | Tests de composants (Vitest) et 6 parcours de bout en bout (Playwright, [journal](../../frontend/e2e/resultats/journal-cluster.txt)) |
| [`tests/load/`](../../tests/load/README.md) | Charge et disponibilité (Locust) |

**Preuves mesurées** (tests verts)

| Type de test | Résultat | Source |
| --- | --- | --- |
| Unitaires, API, sécurité et intégration, `catalog-service` | 289 passed, couverture de 98,45 % | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) |
| Idem, `notification-service` | 203 passed, couverture de 97,66 % | idem |
| `catalog-service` relancé le 11/11/2026 sur le dépôt actuel (après les corrections de la phase 9) | 294 passed, couverture de 98,66 %, Ruff et `mypy --strict` sans erreur | [fiche P10-01, journal](../suivi/taches/P10-01.md) |
| Acceptation | 17 passed | idem |
| Front, composants (Vitest) | 62 tests passés | idem |
| Front, bout en bout (Playwright) | 6 parcours sur 6 | idem |
| Charge (Locust) | tous les seuils respectés | [résumé de la charge](../../tests/load/resultats/20261106-1106/resume.md) |
| Sécurité (SAST, dépendances, image, audit dynamique) | quality gate SonarCloud passée, Trivy et ZAP rejoués | [rapport des scans](../06-securite/rapport-scans.md) |

**Limites assumées.** Playwright et Locust tournent ponctuellement sur le cluster, hors CI (décision du 31/10/2026) ; le job `acceptance` utilise la pile `docker compose`, pas le cluster.

## 8. Validation de la remédiation des risques de sécurité

**Pour 5/5** : le plan de remédiation priorise les actions pour réduire les risques critiques du parc applicatif du SI ; le POC intègre au moins deux bonnes pratiques de sécurité.

| Où le trouver | Ce que c'est |
| --- | --- |
| [Analyse de risques](../06-securite/analyse-risques.md) | Actifs, échelles, flux, STRIDE, correspondance OWASP Top 10 et API Security Top 10, registre de 62 risques notés sur tout le SI (POC, plateforme cible, système existant) |
| [Plan de remédiation](../06-securite/plan-remediation.md) | Méthode de priorisation, matrice impact × probabilité, 58 actions à court, moyen et long terme, budget, suivi. [Matrice des risques](../06-securite/img/matrice-risques.svg) |
| [Bonnes pratiques déjà dans le POC](../06-securite/plan-remediation.md#7-déjà-appliqué-dans-le-poc) | Chacune avec sa preuve (fichier et ligne, test, run) |
| [Rapport des scans](../06-securite/rapport-scans.md) | Audit dynamique (OWASP ZAP), Trivy, SonarCloud, `npm audit`, rejouable par [`run-scans.sh`](../06-securite/scans/run-scans.sh) ; état avant et après corrections |

**Preuves mesurées**

| Mesure | Valeur | Source |
| --- | --- | --- |
| Registre des risques | 62 risques, dont 7 critiques et 30 élevés | [plan de remédiation](../06-securite/plan-remediation.md) |
| Actions du plan | 58 actions, 225,5 j de charge | idem |
| Résultat attendu à 12 mois | criticité cumulée de 650 aujourd'hui à 298, risques critiques de 7 à 0 | idem |
| Bonnes pratiques prouvées dans le POC | 17 (« dix-sept ») | idem |
| Constats de l'audit | 25 constats qualifiés | [index de `docs/06-securite`](../06-securite/README.md) |
| Vulnérabilités avec correctif disponible, avant puis après les corrections de P9-02 | 11 lignes par service avant, 0 après (tableau « Lignes avec correctif ») | [rapport des scans, section 10](../06-securite/rapport-scans.md#10-après-corrections-p9-02) |

**Limites assumées.** Les vulnérabilités sans correctif ne sont pas corrigeables : 201 (89 CVE) lignes par service, dont 11 CVE de sévérité HIGH, suivies au plan. L'état du système d'information existant est **inconnu** : le plan le traite par des hypothèses, dont la vérification est sa première action.

## 9. Cohérence de la gestion des compétences

**Pour 5/5** : les compétences de l'équipe sont recensées, les expertises à acquérir identifiées, au moins une action de formation proposée.

| Où le trouver | Ce que c'est |
| --- | --- |
| [Matrice de compétences](../05-competences/matrice.md) | Échelle de niveaux, 26 compétences évaluées pour chaque membre de l'équipe IT, écarts, criticité, analyse des écarts, 3 recrutements envisagés, matrice cible |
| [Plan de formation](../05-competences/plan-formation.md) | « Déployer, exploiter et relire une application sur Kubernetes avec Helm » : objectifs, 6 modules, modalités, évaluation des acquis, budget, suivi |

**Preuves mesurées**

| Mesure | Valeur | Source |
| --- | --- | --- |
| Action de formation | 28 heures, six modules, sur 6 semaines | [plan de formation](../05-competences/plan-formation.md) |
| Recrutements | trois profils : DevOps/SRE, QA automaticien·ne, UX/UI | [matrice](../05-competences/matrice.md) |

**Limites assumées.** Les profils de Dev 1 et Dev 2 sont des **hypothèses** (le contexte ne les décrit pas), signalées comme telles dans la matrice.

## 10. Qualité de la présentation

**Pour 5/5** : schémas et tableaux lisibles et adaptés à l'oral, démonstration préparée, discours structuré au vocabulaire précis.

| Support | Fichiers |
| --- | --- |
| Architecture | [POC](../02-architecture/img/architecture-poc.svg), [cible](../02-architecture/img/architecture-cible.svg), [placement des nœuds](../02-architecture/img/placement-noeuds.svg), [topologie RabbitMQ](../02-architecture/img/topologie-rabbitmq.svg) |
| Parcours et flux | [publication d'un article](../02-architecture/img/sequence-publication.svg), [authentification OIDC](../02-architecture/img/sequence-authentification.svg), [cycle de vie d'un article](../02-architecture/img/cycle-vie-article.svg) |
| Données | [catalog](../02-architecture/img/donnees-catalog.svg), [notification](../02-architecture/img/donnees-notification.svg) |
| Processus | [pipeline CI/CD](../01-qualite/img/pipeline-cicd.svg), [pipeline backend](../01-qualite/img/pipeline-backend.svg), [cycle DevSecOps](../01-qualite/img/cycle-devsecops.svg), [pyramide des tests](../01-qualite/img/pyramide-tests.svg) |
| Sécurité | [matrice des risques](../06-securite/img/matrice-risques.svg) |
| Application | [7 captures d'écran](../../frontend/e2e/resultats/captures/) du parcours complet |
| Observabilité | [captures Grafana](../04-experimentations/05-charge-disponibilite/resultats/20261106-1132/grafana-pic-catalog-service.png) |

**Démonstration.** Elle s'appuie sur le cluster déployé par les commandes du [README](../../README.md) : application sur `https://app.127.0.0.1.sslip.io`, comptes `admin`, `alice`, `bob` et `chloe`, Grafana, `kubectl get hpa`. Les parcours à montrer sont décrits dans la section « Utiliser l'application » du README ; le journal Playwright et les captures prouvent qu'ils fonctionnent.

**Vocabulaire à maîtriser** (définitions dans les documents cités) : *HPA* et sondes `liveness` et `readiness` ([architecture du POC](../02-architecture/architecture-poc.md)) ; OIDC, PKCE et validation locale du JWT ([ADR 0004](../02-architecture/adr/0004-keycloak.md)) ; *outbox* et publication après commit, limite L2 ([architecture du POC](../02-architecture/architecture-poc.md#8-limites-assumées-du-poc)) ; STRIDE ([analyse de risques](../06-securite/analyse-risques.md)) ; ISO 25010 ([indicateurs](../01-qualite/indicateurs.md)).

## Parcours de lecture en 10 minutes

| Minute | Lire ou lancer | Pour voir |
| --- | --- | --- |
| 0 à 1 | [README](../../README.md), en-tête et schéma | Ce que fait le POC et comment il est bâti |
| 1 à 2 | [Architecture du POC](../02-architecture/architecture-poc.md), sections 1 et 4 | Découpage, communication, disponibilité (critères 2 et 5) |
| 2 à 3 | [Captures](../../frontend/e2e/resultats/captures/) puis [user stories](../03-backlog/user-stories.md) | La fonctionnalité métier (critère 3) |
| 3 à 4 | [Schéma CI/CD](../01-qualite/cicd.md) puis [conformité](../01-qualite/conformite-pipeline.md) | Le pipeline et sa preuve (critère 4) |
| 4 à 5 | [Protocole 5](../04-experimentations/05-charge-disponibilite/protocole.md), tableau de l'index | Montée en charge et pod supprimé (critères 1 et 5) |
| 5 à 6 | [Indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) | Les 5 indicateurs et leurs axes d'amélioration (critère 6) |
| 6 à 7 | [Processus de test](../01-qualite/processus-test.md) | Types de tests, outils, RACI (critère 7) |
| 7 à 9 | [Plan de remédiation](../06-securite/plan-remediation.md), « Lecture rapide » et section 7 | 58 actions et 17 bonnes pratiques (critère 8) |
| 9 à 10 | [Matrice](../05-competences/matrice.md) et [plan de formation](../05-competences/plan-formation.md) | Compétences et formation (critère 9) |

Pour aller plus loin, la section « Utiliser l'application » du [README](../../README.md) donne les adresses et les comptes pour essayer l'application soi-même.

## Contrôler ce guide

```bash
python3 -I docs/07-soutenance/verifier-guide.py
```

Le script contrôle que chaque lien relatif du guide et du README existe (et chaque ancre), puis que chaque chiffre de sa liste figure dans le fichier source cité. Il retourne un code non nul au premier écart.
