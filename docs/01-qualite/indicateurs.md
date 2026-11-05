# Indicateurs qualité

Cinq indicateurs mesurent la qualité du POC. Chacun est rattaché à une caractéristique de la norme ISO/IEC 25010:2023, a un seuil, un outil de mesure et une action en cas de dépassement. Les seuils reprennent **sans les modifier** les exigences non fonctionnelles de [exigences.md](../03-backlog/exigences.md) (ENF-05, 12, 13, 22, 23) et les critères d'acceptation de [user-stories.md](../03-backlog/user-stories.md).

Un indicateur n'est utile que s'il est mesuré à chaque modification, comparé à un seuil et suivi dans le temps. C'est ce suivi qui empêche l'accumulation de la dette technique : une dérive est visible dès le commit qui la crée, pas en fin de projet.

Les valeurs réelles sont relevées dans la section « Relevés » : I1, I2 (Ruff et mypy), I4 et I5 depuis la phase 5 (CI), I2 (SonarCloud) après la tâche P5-04, I3 en phase 8. Les définitions et les seuils plus haut ne changent pas.

## Synthèse

| # | Indicateur | Caractéristique ISO 25010 (sous-caractéristique) | Seuil | Outil | Moment de mesure | ENF liée |
| --- | --- | --- | --- | --- | --- | --- |
| I1 | Couverture de tests du code métier | Maintenabilité (testabilité) | ≥ 80 % | pytest-cov, SonarCloud | Chaque push et pull request (CI) | ENF-22 |
| I2 | Dette technique | Maintenabilité (analysabilité, modifiabilité) | Note de maintenabilité A ; duplication < 3 % ; complexité cognitive ≤ 15 par fonction ; Ruff et mypy sans erreur | SonarCloud, Ruff, mypy (mode strict) | Chaque push et pull request (CI) | ENF-23 |
| I3 | Latence p95 et taux d'erreur sous charge | Efficacité de performance (comportement temporel, capacité) ; Fiabilité (disponibilité) | Avec 50 utilisateurs Locust : p95 < 300 ms en lecture du catalogue, p95 < 500 ms en publication d'article, moins de 1 % de réponses 5xx | Locust, Prometheus, Grafana | Test de charge de la phase 8 et démo de disponibilité | ENF-12, ENF-13 |
| I4 | Vulnérabilités CRITICAL et HIGH | Sécurité (résistance) | 0 vulnérabilité CRITICAL ou HIGH avec correctif disponible et 0 secret de sévérité CRITICAL ou HIGH (Trivy bloquant, ENF-04 et ENF-05) | Trivy, SonarCloud | Chaque push et pull request (CI) | ENF-04, ENF-05 |
| I5 | Taux de critères d'acceptation validés | Adéquation fonctionnelle (complétude fonctionnelle, exactitude fonctionnelle) | 17 critères sur 17 passent | Tests d'acceptation pytest + httpx | CI et avant chaque démonstration | [user-stories.md](../03-backlog/user-stories.md) |

Outils du POC cités ici : ceux de la stack décidée (pytest, pytest-cov, SonarCloud, Ruff, mypy, Locust, Prometheus, Grafana, Trivy, pytest + httpx). Les versions seront figées par `uv.lock` (backend), `package.json` (front) et les workflows GitHub Actions (phases 3 à 5), puis consignées dans les protocoles de `docs/04-experimentations`.

## I1 — Couverture de tests du code métier

| Rubrique | Contenu |
| --- | --- |
| Caractéristique ISO 25010 | Maintenabilité, sous-caractéristique testabilité |
| Définition | Part des lignes (et des branches) du code métier exécutées par les tests automatisés |
| Formule | `lignes couvertes / lignes exécutables × 100`, calculée sur `services/*/src`, hors code de configuration et de démarrage |
| Seuil | ≥ 80 % (ENF-22) |
| Justification du seuil | Au-dessous, les règles de gestion (contrôle automatique, historique des prix, dédoublonnage des notifications) risquent de n'être vérifiées par aucun test. Au-dessus de 80 %, le gain marginal est faible pour un POC. |
| Outil | pytest-cov (mesure), SonarCloud (affichage et quality gate) |
| Où et quand | Job `test` de la CI GitHub Actions, à chaque push et pull request. Rapport XML transmis à SonarCloud par le job `sonar`. |
| Qui suit | Lead Developer, à la revue de fin de sprint |
| Action si le seuil n'est pas respecté | Le job `test` échoue lui-même sous 80 % (`pytest --cov-fail-under=80`), et la quality gate SonarCloud bloque aussi le pipeline : aucune image n'est publiée sur GHCR. Les tests manquants sont écrits avant la fusion. |
| Effet sur la dette technique | Une couverture qui baisse signale du code ajouté sans test. Le suivi par pull request (couverture du code nouveau) empêche de repousser les tests à plus tard : une régression sur un contrôle métier est détectée par la CI et non en production. Il permet aussi de refactorer les services sans crainte de casser un comportement non vérifié. |

## I2 — Dette technique SonarCloud

| Rubrique | Contenu |
| --- | --- |
| Caractéristique ISO 25010 | Maintenabilité, sous-caractéristiques analysabilité et modifiabilité |
| Définition | Effort estimé pour corriger les défauts de maintenabilité (« code smells ») détectés par l'analyse statique, et qualité du typage et du style du code |
| Formules | Ratio de dette = `coût de remédiation / coût de développement estimé` ; note de maintenabilité de A (ratio ≤ 5 %) à E (barème SonarCloud) ; duplication = `lignes dupliquées / lignes totales × 100` ; complexité cognitive mesurée par fonction |
| Seuil | Note de maintenabilité A ; duplication < 3 % ; complexité cognitive ≤ 15 par fonction ; Ruff et mypy (mode strict) sans erreur (ENF-23) |
| Justification du seuil | La note A signifie un ratio de dette faible. Une complexité cognitive de 15 est le seuil par défaut de SonarCloud : au-delà, une fonction devient difficile à relire et à tester. La duplication sous 3 % évite de corriger le même défaut à plusieurs endroits. |
| Outils | SonarCloud (note, ratio, duplication, complexité), Ruff (style et erreurs courantes), mypy en mode strict (typage) |
| Où et quand | Ruff et mypy : job `lint`, première étape de la CI, bloquant. SonarCloud : job `sonar`, après les tests, quality gate bloquante. À chaque push et pull request. |
| Qui suit | Lead Developer, à la revue de fin de sprint |
| Action si le seuil n'est pas respecté | Ruff ou mypy en échec : le pipeline s'arrête avant les tests. Quality gate SonarCloud en échec : pas de publication d'image. Une dette acceptée volontairement est notée comme ticket de dette avec sa justification. |
| Effet sur la dette technique | C'est l'indicateur direct de la dette. La quality gate s'applique au code nouveau : chaque pull request est contrôlée sur ses propres lignes, ce qui empêche la dette de s'accumuler par petites touches. Le ratio suivi dans le temps montre la tendance. mypy strict évite les erreurs de type qui se paieraient plus tard en corrections. |

## I3 — Latence p95 et taux d'erreur sous charge

| Rubrique | Contenu |
| --- | --- |
| Caractéristique ISO 25010 | Efficacité de performance (comportement temporel, capacité) ; Fiabilité (disponibilité) |
| Définition | Latence au 95e percentile des requêtes de lecture du catalogue et de publication d'article, et part des réponses 5xx, sous charge nominale |
| Formules | p95 : durée en dessous de laquelle se terminent 95 % des requêtes du scénario ; taux d'erreur = `réponses 5xx / requêtes totales × 100` |
| Seuil | Avec 50 utilisateurs simultanés (Locust) : p95 < 300 ms en lecture du catalogue (ENF-12), p95 < 500 ms en publication d'article (ENF-12), moins de 1 % de réponses 5xx (ENF-13) |
| Justification du seuil | Une lecture du catalogue est une requête simple sur PostgreSQL : 300 ms laisse une marge confortable. La publication inclut le contrôle automatique, l'écriture en base et la publication de l'événement RabbitMQ juste après le commit : 500 ms. Le p95 reflète l'expérience de la quasi-totalité des utilisateurs, contrairement à la moyenne. |
| Outils | Locust (génération de charge et statistiques), Prometheus, fourni par kube-prometheus-stack (métriques `/metrics` des services), Grafana (tableau de bord : débit, latence p95, taux d'erreur) |
| Où et quand | Test de charge de la phase 8 sur le cluster k3d, rejoué lors de la démo de disponibilité (suppression d'un pod, montée de l'HPA). Résultats archivés dans `tests/load`. |
| Qui suit | Lead Developer |
| Action si le seuil n'est pas respecté | Ticket de dette ouvert avec la mesure, le scénario et l'hypothèse de cause (requête SQL, index, ressources du pod). Correction puis nouveau test avant la soutenance. |
| Effet sur la dette technique | La dette de performance est invisible tant qu'on ne mesure pas : une requête lente passe en revue sans alerte. Rejouer le même scénario Locust avec les mêmes seuils permet de comparer les relevés et de détecter une régression de latence introduite entre deux versions, avant qu'elle ne soit figée dans l'architecture. |

## I4 — Vulnérabilités CRITICAL et HIGH

| Rubrique | Contenu |
| --- | --- |
| Caractéristique ISO 25010 | Sécurité, sous-caractéristique résistance |
| Définition | Nombre de vulnérabilités connues de sévérité CRITICAL ou HIGH, avec correctif disponible, dans les dépendances et les images Docker, auquel s'ajoutent les problèmes de sécurité détectés par l'analyse statique SonarCloud |
| Formule | Décompte bloquant (Trivy) : `nombre de vulnérabilités CRITICAL + HIGH avec correctif + nombre de secrets CRITICAL + HIGH`. Les problèmes de sécurité ouverts à la quality gate SonarCloud sont suivis en complément, sans seuil propre |
| Seuil | 0 vulnérabilité CRITICAL ou HIGH avec correctif disponible et 0 secret de sévérité CRITICAL ou HIGH, Trivy bloquant (ENF-04 et ENF-05) |
| Justification du seuil | Une vulnérabilité sévère avec correctif disponible peut être supprimée sans coût fonctionnel : la tolérer est un choix, pas une contrainte. Celles sans correctif sont consignées dans le plan de remédiation, car aucune action immédiate n'est possible. |
| Outils | Trivy (dépendances, image, secrets), SonarCloud (analyse statique du code) |
| Où et quand | Job `build-scan` de la CI (Trivy), après le build Docker et avant le push sur GHCR (job `publish`), à chaque push et pull request |
| Qui suit | Lead Developer, à la revue de fin de sprint |
| Action si le seuil n'est pas respecté | Le pipeline est bloqué : aucune image n'est publiée. Mise à jour de la dépendance ou de l'image de base. Si aucun correctif n'existe, la vulnérabilité est inscrite au plan de remédiation (`docs/06-securite`) avec sa priorité. |
| Effet sur la dette technique | Une dépendance obsolète est une dette qui s'aggrave avec le temps : des vulnérabilités s'y ajoutent et la mise à jour devient plus risquée. L'analyse à chaque modification, y compris sans changement de code, oblige à des montées de version petites et fréquentes plutôt qu'à une migration lourde. |

## I5 — Taux de critères d'acceptation validés

| Rubrique | Contenu |
| --- | --- |
| Caractéristique ISO 25010 | Adéquation fonctionnelle, sous-caractéristiques complétude fonctionnelle et exactitude fonctionnelle |
| Définition | Part des critères d'acceptation du backlog qui sont vérifiés par un test d'acceptation passant |
| Formule | `critères validés / critères définis × 100`, soit 17 critères pour les 5 user stories de [user-stories.md](../03-backlog/user-stories.md) |
| Seuil | 17 critères sur 17 passent |
| Justification du seuil | Chaque critère décrit un comportement attendu du métier Collector (par exemple le rejet d'un article avec coordonnées). Un critère non validé est une fonctionnalité soit absente, soit incorrecte : aucun écart n'est acceptable pour la démonstration. |
| Outil | Tests d'acceptation pytest + httpx dans `tests/acceptance`, nommés d'après la story et le critère (`test_us03_ca2_article_avec_coordonnees_rejete`) |
| Où et quand | En CI : job `acceptance` qui démarre une pile `docker compose` (PostgreSQL, RabbitMQ, Keycloak, les 2 services), puis lance `tests/acceptance`. Avant chaque démonstration contre le cluster local |
| Qui suit | Lead Developer |
| Action si le seuil n'est pas respecté | Le test en échec bloque la fusion. Soit le code est corrigé, soit le critère est révisé dans le backlog avec une décision documentée. |
| Effet sur la dette technique | Le nom des tests relie chaque critère à une preuve exécutable. Si un refactoring ou une montée de version casse un comportement métier, le critère correspondant échoue immédiatement. La dette fonctionnelle (écart entre backlog et code) ne peut donc pas s'installer en silence. |

## Suivi dans le temps

| Indicateur | Où voir la valeur | Fréquence |
| --- | --- | --- |
| I1, I2 | Tableau de bord du projet SonarCloud (historique, tendance du ratio de dette) | À chaque analyse CI |
| I4 | Journal du job `build-scan` (Trivy) dans la CI ; SonarCloud pour l'analyse statique | À chaque exécution du pipeline |
| I5 | Rapport pytest dans les artefacts de la CI | À chaque exécution du pipeline |
| I3 | Grafana pendant le test de charge ; résultats Locust archivés dans `tests/load` | À chaque campagne de charge (phase 8) |

Revue de fin de sprint : le Lead Developer relève les cinq valeurs, les compare aux seuils, inscrit le résultat dans la section « Relevés » et ouvre un ticket de dette pour chaque indicateur hors seuil, avec une échéance.

## Relevés

### Mesures du 04/11/2026 (phase 5, CI)

Source unique : le run de `main` [41825781085](https://github.com/Luucaaas/collector-poc/actions/runs/41825781085) (commit `49df273`, 9 jobs verts), dont les journaux et les artefacts ont été relus le 04/11/2026. Le déroulé complet du pipeline est dans [conformite-pipeline.md](conformite-pipeline.md).

| Indicateur | Mesure | Seuil | Verdict | Source |
| --- | --- | --- | --- | --- |
| I1 couverture, `catalog-service` | **99,06 %** des lignes (843 sur 851), 270 tests passés | ≥ 80 % | Atteint | Journal du job `test (catalog-service)` : « Total coverage: 99.06% » ; artefact `coverage-catalog-service` (`lines-valid="851" lines-covered="843"`) |
| I1 couverture, `notification-service` | **98,43 %** des lignes (690 sur 701), 186 tests passés | ≥ 80 % | Atteint | Journal du job `test (notification-service)` : « Total coverage: 98.43% » ; artefact `coverage-notification-service` |
| I2 Ruff | **0 erreur** (`ruff check .`), formatage conforme (36 fichiers catalog, 31 notification, 9 pour `tests/acceptance`) | 0 erreur | Atteint | Journaux de `lint` et d'`acceptance` : « All checks passed! », « files already formatted » |
| I2 mypy `--strict` | **0 erreur** sur 19 fichiers (catalog), 15 (notification) et 8 (`tests/acceptance`) | 0 erreur | Atteint | « Success: no issues found in N source files » |
| I2 SonarCloud, `catalog-service` | Notes fiabilité, sécurité, maintenabilité **A** ; dette 0 min ; duplication **0,0 %** ; 0 bug, 0 vulnérabilité, 0 hotspot, 0 code smell ; quality gate OK | Note A, duplication < 3 % | Atteint (complexité cognitive par fonction : aucune règle signalée, mesure indirecte) | Pull request n°1, run [42037655092](https://github.com/Luucaaas/collector-poc/actions/runs/42037655092) ; `api/measures/component?component=Luucaaas_collector-poc_catalog-service&metricKeys=...&pullRequest=1`, mesure du 05/11/2026. À relever de nouveau sur `main` après fusion |
| I2 SonarCloud, `notification-service` | Mêmes valeurs : notes **A**, dette 0 min, duplication **0,0 %**, 0 / 0 / 0 / 0, quality gate OK | Note A, duplication < 3 % | Atteint | Idem, clé `Luucaaas_collector-poc_notification-service` |
| I2 SonarCloud, `main` avant P5-06 | `catalog-service` : **2 code smells** (`python:S8414` BLOCKER, `python:S8786` MAJOR), dette 25 min ; `notification-service` : **1 code smell** (`python:S8414`), dette 5 min ; 0 bug, 0 vulnérabilité, 0 hotspot, duplication 0,0 %, notes A | Note A, duplication < 3 % | Atteint (note A) mais 3 constats ouverts, traités en axe d'amélioration | `api/issues/search?componentKeys=<clé>&branch=main&resolved=false`, relevé du 05/11/2026 sur le run de `main` [42039814860](https://github.com/Luucaaas/collector-poc/actions/runs/42039814860) |
| I2 SonarCloud, pull request n°2 (P5-06) | Les deux services : **0 code smell**, dette 0 min, 0 bug, 0 vulnérabilité, 0 hotspot, duplication 0,0 %, notes A, couverture 98,5 % et 97,6 % ; `api/issues/search?componentKeys=<clé>&pullRequest=2&resolved=false` renvoie `total: 0` | 0 constat | Atteint sur la pull request. **À relever sur `main` après fusion** (le chef) | Run de la pull request [42043594738](https://github.com/Luucaaas/collector-poc/actions/runs/42043594738), relevé du 05/11/2026 |
| I1 couverture SonarCloud (lignes et branches) | `catalog-service` **98,5 %** (lignes 99,1 %, branches 94,5 %) ; `notification-service` **97,6 %** (lignes 98,4 %, branches 91,1 %) | ≥ 80 % | Atteint | Mêmes appels (`coverage`, `line_coverage`, `branch_coverage`). pytest-cov avec `branch = true` : 98,47 % et 97,60 % (run de la PR [42037655092](https://github.com/Luucaaas/collector-poc/actions/runs/42037655092)) |
| I4 vulnérabilités CRITICAL et HIGH avec correctif | **0** dans chaque image : `debian 13.7` et 41 paquets Python analysés, 0 vulnérabilité | 0 | Atteint | Tableau « Report Summary » de Trivy 0.76.0 dans `build-scan` |
| I4 secrets CRITICAL ou HIGH | **0** (colonne Secrets sans constat, code de sortie 0) | 0 | Atteint | Même journal |
| I5 critères d'acceptation | **17 sur 17** (100 %), 0 échec, 0 ignoré, en 9,5 s ; 5 stories couvertes | 17 sur 17 | Atteint | Journal « 17 passed in 9.50s » ; artefact `junit-acceptance` |

Le blocage de ces seuils est démontré par des runs rouges pour Ruff ([41818132153](https://github.com/Luucaaas/collector-poc/actions/runs/41818132153)) et Trivy ([41821035266](https://github.com/Luucaaas/collector-poc/actions/runs/41821035266)). Les seuils de couverture et d'acceptation sont vérifiés à chaque run mais n'ont pas été cassés volontairement.

#### Limites de la mesure

- **I1** : les valeurs du run 41825781085 sont des taux de lignes (`branches-valid="0"`). `branch = true` est activé depuis P5-04 (`[tool.coverage.run]`) : la couverture combinée des lignes et des branches est de l'ordre de 98 % (SonarCloud : 98,5 % et 97,6 %), avec 94,5 % et 91,1 % pour les seules branches. Les branches `if` non exercées sont maintenant visibles.
- **I2** : SonarCloud mesure la duplication. La complexité cognitive n'est pas renvoyée comme mesure par l'API sur une pull request : elle est contrôlée indirectement par la règle « Cognitive Complexity of functions should not be too high » (seuil 15) du profil Sonar way, qui n'a levé aucun problème (0 code smell). Les mesures ci-dessus portent sur la pull request n°1 (analyse du code modifié) : le plan Free n'analyse que `main` et les pull requests, pas les autres branches. Le nom du projet catalog (« ollector-poc ») reste à corriger côté SonarCloud.
- **I4** : `--ignore-unfixed` écarte les vulnérabilités sans correctif ; elles ne sont donc pas comptées par cette mesure. Seule l'image amd64 est scannée (l'arm64, construite au `publish`, ne l'est pas). Trivy 0.76.2 est sortie (relevé du 05/11/2026) : la 0.76.0 n'est plus la dernière ; la montée de version est volontaire (nouvelle somme SHA-256 à relever), comme pour les digests.
- **I5** : les 17 tests tournent sur une pile `docker compose` (une seule instance de chaque brique), pas sur le cluster k3d ; ils prouvent l'adéquation fonctionnelle, pas la tenue en charge (I3).

#### Axes d'amélioration contre la dette technique

| Indicateur | Écart ou risque constaté | Action | Échéance |
| --- | --- | --- | --- |
| I1 | Branches désormais mesurées (`branch = true`) : 94,5 % (catalog) et 91,1 % (notification) | Lister les branches partielles (`--cov-report=term-missing`) et tester celles qui portent une règle métier | Phase 8 |
| I1 | 8 lignes non couvertes (catalog) et 11 (notification) | Lister les lignes (`--cov-report=term-missing`), tester celles qui portent une règle métier, justifier les autres | Phase 8 |
| I1 | Le seuil de 80 % est très inférieur à la valeur mesurée (98 %) : il tolérerait une baisse de 18 points sans alerte | Fait en partie : la quality gate SonarCloud contrôle la couverture du code nouveau (≥ 80 %), blocage démontré (run 42037061364). Remonter le seuil global à 95 % reste possible | Clos (P5-04) |
| I2 | Duplication et complexité non vérifiées | Fait : job `sonar` (P5-04), duplication 0,0 % | Clos (P5-04) |
| I2 | Constats SonarCloud de `main` (première analyse complète, invisibles sur la pull request n°1) : 3 code smells, dette 30 min (catalog 2 : `python:S8414` BLOCKER et `python:S8786` MAJOR ; notification 1 : `python:S8414`) | Fait (P5-06, pull request n°2) : `CORSMiddleware` ajouté en dernier dans les deux services ; `_EMAIL` ancré sur l'arobase et `_is_national` en temps linéaire, avec un test de performance (pire cas de 100 000 caractères : 24 s avant, 2 ms après pour `_EMAIL`). Résultat sur la pull request : voir « Relevés ». Cycle mesure, axe, correction, nouvelle mesure | Clos (P5-06) |
| I2 | mypy strict ne couvre pas le code des tests des services | Étendre `mypy --strict` aux dossiers `tests/` des services, progressivement, ou documenter l'exclusion | Phase 8 |
| I4 | Base de vulnérabilités de Trivy non épinglée ; Trivy 0.76.0 n'est plus la dernière version ; arm64 non scanné ; vulnérabilités sans correctif invisibles | Mise à jour volontaire de Trivy (version, somme SHA-256) à chaque revue ; rapport complet sans `--ignore-unfixed` consigné au plan de remédiation ; scan de l'arm64 au `publish` en cible | Phase 9 |
| I5 | Les tests ne tournent pas sur le cluster | Rejouer les 17 critères contre le cluster k3d avant la démonstration (déjà prévu dans la définition d'I5) | Phase 6 |

### Relevés de fin de sprint

Rempli en phase 8 pour I3 ; les valeurs ci-dessus sont reprises et mises à jour à chaque revue.

| Date | I1 | I2 | I3 | I4 | I5 | Commentaire |
| --- | --- | --- | --- | --- | --- | --- |
| 04/11/2026 | 99,06 % (catalog), 98,43 % (notification) | Ruff 0, mypy 0 ; SonarCloud à compléter | Phase 8 | 0 CRITICAL ou HIGH, 0 secret | 17 sur 17 | Run 41825781085 (`main`, `49df273`) |
