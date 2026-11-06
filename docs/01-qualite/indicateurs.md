# Indicateurs qualité

Cinq indicateurs mesurent la qualité du POC. Chacun est rattaché à une caractéristique de la norme ISO/IEC 25010:2023, a un seuil, un outil de mesure et une action en cas de dépassement. Les seuils reprennent **sans les modifier** les exigences non fonctionnelles de [exigences.md](../03-backlog/exigences.md) (ENF-05, 12, 13, 22, 23) et les critères d'acceptation de [user-stories.md](../03-backlog/user-stories.md).

Un indicateur n'est utile que s'il est mesuré à chaque modification, comparé à un seuil et suivi dans le temps. C'est ce suivi qui empêche l'accumulation de la dette technique : une dérive est visible dès le commit qui la crée, pas en fin de projet.

Les valeurs réelles sont relevées dans la section « Relevés » : I1, I2 (Ruff et mypy), I4 et I5 depuis la phase 5 (CI), I2 (SonarCloud) après la tâche P5-04, et les cinq indicateurs sur une même version en phase 8 (relevé du 06/11/2026, le plus récent). Les définitions et les seuils plus haut ne changent pas.

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

### Mesures du 06/11/2026 (phase 8)

**Version mesurée.** Les cinq indicateurs portent sur le même état du POC : le commit `22364bc` de `main`, avec deux runs verts relus le 06/11/2026 (13:47).

| Élément | Valeur |
| --- | --- |
| Run `backend` | [42219458020](https://github.com/Luucaaas/collector-poc/actions/runs/42219458020), 11 jobs verts (`lint`, `test`, `sonar`, `build-scan`, `acceptance`, `publish`) |
| Run `frontend` | [42219458005](https://github.com/Luucaaas/collector-poc/actions/runs/42219458005), 2 jobs verts (`frontend`, `publish`) |
| Image `catalog-service` | `ghcr.io/luucaaas/catalog-service:sha-22364bc`, `sha256:0dd998040c65a6585fe9c7b036860c86f0ef7d4ac5ef9fe8c5ddfade7cc02d46` |
| Image `notification-service` | `ghcr.io/luucaaas/notification-service:sha-22364bc`, `sha256:cb1d710ebf8a6b4d90a3926bc4a59a90716801d39c4111fbe2b441663137f418` |
| Image `frontend` | `ghcr.io/luucaaas/frontend:sha-22364bc`, `sha256:51ed3dbe83ad2fe4e91f269446341c9612063ff3bb300feb369fdcb388eaaa4a` (amd64 et arm64) |

Les digests viennent des étapes « Résumé » des jobs `publish` (les services sont publiés en amd64 et arm64 par le workflow, conformément au contrat). Seul le job `publish` du front scanne le digest publié (étapes « Trivy sur le digest publié » en amd64 et en arm64) ; celui du backend n'a pas d'étape Trivy (limite de l'arm64 des services, plus bas).

**Lien avec les mesures de charge (I3).** Les exécutions de charge de P8-02 et P8-03 ont été faites sur les images `sha-9d2c96e`, pas sur `sha-22364bc`. Entre les deux commits, `git diff --stat 9d2c96e 22364bc -- services/` est **vide** : le code et les dépendances des deux services sont identiques. Pour le front, `git diff --stat 9d2c96e 22364bc -- frontend/src frontend/Dockerfile frontend/package.json frontend/package-lock.json` est lui aussi vide ; les différences touchent `frontend/e2e/` et `playwright.config.ts` (captures Grafana, hors de l'image), la limite mémoire de Grafana (`deploy/infra/monitoring/kube-prometheus-stack.yaml`) et la suppression de copies de synchronisation « nom 2 ». Les commits de branche cités dans les résultats bruts de charge (`d8eb5ec`, `9f04231`) ne sont plus dans l'historique (fusions en squash) ; les références durables sont `9d2c96e` (images), `517c924` et `bc46aed` (fusions). Les mesures de charge s'appliquent donc au code de `22364bc` ; seuls les digests des images diffèrent (reconstruites par la CI). Les parcours Playwright de P7-05 ont été exécutés sur `sha-cd5751f` (06/11/2026 10:00), plus ancien : voir la ligne d'I5.

| Indicateur | Mesure | Seuil | Verdict | Source |
| --- | --- | --- | --- | --- |
| I1 couverture, `catalog-service` (pytest-cov) | Lignes **99,06 %** (840 sur 848), branches **94,17 %** (113 sur 120), couverture combinée **98,45 %** ; 289 tests passés | ≥ 80 % | Atteint | Run 42219458020, job `test (catalog-service)` : « Total coverage: 98.45% », « 289 passed » ; artefact `coverage-catalog-service` (`lines-valid="848" lines-covered="840" branches-valid="120" branches-covered="113"`) |
| I1 couverture, `notification-service` (pytest-cov) | Lignes **98,47 %** (708 sur 719), branches **91,49 %** (86 sur 94), combinée **97,66 %** ; 203 tests passés | ≥ 80 % | Atteint | Job `test (notification-service)` : « Total coverage: 97.66% », « 203 passed » ; artefact `coverage-notification-service` |
| I1 couverture SonarCloud (`main`) | `catalog-service` **98,5 %** (lignes 99,1, branches 94,2) ; `notification-service` **97,7 %** (lignes 98,5, branches 91,5) | ≥ 80 % | Atteint | `curl -s "https://sonarcloud.io/api/measures/component?component=Luucaaas_collector-poc_<service>&branch=main&metricKeys=coverage,line_coverage,branch_coverage,..."`, API publique sans jeton, relevé du 06/11/2026 ; analyse de `main` du 06/11/2026 12:42 (révision `22364bc`, `api/project_analyses/search`) |
| I2 Ruff | **0 erreur** ; formatage conforme (37 fichiers catalog, 31 notification, 9 `tests/acceptance`) | 0 erreur | Atteint | Jobs `lint` et `acceptance` : « All checks passed! », « files already formatted » |
| I2 mypy `--strict` | **0 erreur** : 19 fichiers (catalog), 15 (notification), 8 (`tests/acceptance`) | 0 erreur | Atteint | « Success: no issues found in N source files ». Les dossiers `tests/` des services ne sont pas contrôlés par la CI : voir « Mesures nouvelles » |
| I2 SonarCloud, `catalog-service` | Quality gate **OK** ; notes fiabilité, sécurité, maintenabilité **A** ; dette **0 min** (ratio 0,0 %) ; duplication **0,0 %** ; 0 bug, 0 vulnérabilité, 0 hotspot, **0 code smell** ; 1 236 lignes de code ; 0 issue ouverte | Note A, duplication < 3 % | Atteint | `api/measures/component`, `api/qualitygates/project_status`, `api/issues/search?...&resolved=false` avec `&branch=main`, relevé du 06/11/2026 ; journal du job `sonar (catalog-service)` : « QUALITY GATE STATUS: PASSED » |
| I2 SonarCloud, `notification-service` | Mêmes valeurs : quality gate **OK**, notes **A**, dette 0 min, duplication **0,0 %**, 0 / 0 / 0 / 0, 0 issue ouverte ; 1 029 lignes de code | Note A, duplication < 3 % | Atteint | Idem, clé `Luucaaas_collector-poc_notification-service` |
| I2 complexité cognitive par fonction | SonarCloud ne donne que le total par fichier (catalog : 117 au total, maximum 43 pour `auth.py` ; notification : 99, maximum 43) ; aucun constat de la règle du profil Sonar way ; **complexité cyclomatique maximale 10** (`verify` de `auth.py`, dans les deux services) | ≤ 15 par fonction | Atteint (mesure indirecte) | `api/measures/component_tree?...metricKeys=cognitive_complexity` ; `ruff check src --select C901 --config "lint.mccabe.max-complexity=N"` en local : 0 fonction au-dessus de 10, 1 au-dessus de 8 par service. La complexité cyclomatique n'est pas la complexité cognitive : simple indice |
| I2 ESLint (front) | **0 erreur, 0 avertissement** (`eslint . --max-warnings 0`) ; `tsc -b` fait partie du build | 0 | Atteint | Run 42219458005, job `frontend`, étape ESLint ; relancé en local (`npm run lint`), sans sortie d'erreur |
| I3 latence de lecture (50 utilisateurs) | p95 de `GET /articles` : **21 ms** (3 034 requêtes) ; autres lectures 13 et 16 ms | < 300 ms | Atteint (marge d'un facteur 14) | `tests/load/resultats/20261106-1106/resume.md` (P8-02, 06/11/2026 11:06, images `sha-9d2c96e` de `main`, plateau de 310 s ; scénarios fusionnés par `517c924`) |
| I3 latence de publication (50 utilisateurs) | p95 de `POST /articles` : **23 ms** (291 requêtes) ; `PUT .../price` 28 ms | < 500 ms | Atteint (marge d'un facteur 21) | Même fichier |
| I3 taux de 5xx (50 utilisateurs) | **0 %** : 0 sur 6 564 requêtes côté Locust, 0 sur 6 630 côté services (Prometheus) | < 1 % | Atteint | Même fichier |
| I3 ENF-14, délai des notifications | **moins de 0,1 s** (p95 interpolé dans le premier seau : 0,095 s) | p95 < 2 s | Atteint | Même fichier (Prometheus) |
| I3 complément, pic de 200 utilisateurs (informatif) | 4 233 requêtes pendant la montée de l'HPA : p95 liste 84 ms, publication 127 ms ; à 5 réplicas : 13 et 16 ms ; **0 réponse 5xx sur 20 235 requêtes** (services) ; 5 réplicas prêts en 60 s | Hors seuil (le seuil vaut pour 50 utilisateurs) | Information | `docs/04-experimentations/05-charge-disponibilite/resultats/20261106-1132/resume.md` (P8-03, images `sha-9d2c96e`, protocole fusionné par `bc46aed`) |
| I3 complément, suppression d'un pod sous charge | Pod remplacé en **4,9 s** (6,2 s pour tous les réplicas prêts), **0 échec sur 533 requêtes** pendant la suppression | Hors seuil | Information | Même fichier |
| I4 Trivy, `catalog-service` et `notification-service` | **0 vulnérabilité CRITICAL ou HIGH avec correctif**, **0 secret** : `debian 13.7` et 41 paquets Python par image, 0 constat sur les 42 cibles du tableau | 0 | Atteint | Run 42219458020, jobs `build-scan`, tableau « Report Summary » de Trivy 0.76.0 (`--scanners vuln,secret --severity CRITICAL,HIGH --ignore-unfixed --exit-code 1`), image amd64 seulement |
| I4 Trivy, image `frontend` (CI) | **0** vulnérabilité, secrets sans constat : cible `collector/frontend:ci (alpine 3.24.2)` | 0 | Atteint | Run 42219458005, job `frontend`, étape « Trivy (paquets de l'OS, secrets) » |
| I4 Trivy, digest publié du front | **0** vulnérabilité, secrets sans constat, sur **amd64 et arm64** : `ghcr.io/luucaaas/frontend@sha256:51ed3dbe…aaa4a (alpine 3.24.2)` | 0 | Atteint | Run 42219458005, job `publish`, étapes « Trivy sur le digest publié (amd64) » et « (arm64) » |
| I4 `npm audit` du front | `npm audit --omit=dev --audit-level=high` : **« found 0 vulnerabilities »** (dépendances embarquées) | 0 HIGH ou plus | Atteint | Run 42219458005, étape « npm audit (dépendances embarquées) » ; rejoué en local le 06/11/2026 : 0 |
| I4 SonarCloud (analyse statique) | 0 vulnérabilité, 0 hotspot, note de sécurité **A** pour les deux services | Suivi, sans seuil propre | Atteint | Mêmes appels que pour I2 |
| I5 critères d'acceptation | **17 sur 17** (100 %), 0 échec, 0 ignoré, en 9,84 s | 17 sur 17 | Atteint | Run 42219458020, job `acceptance` : « 17 passed in 9.83s » ; artefact `junit-acceptance` (`tests="17" failures="0" errors="0" skipped="0"`) |
| I5 complément, parcours Playwright sur le cluster | **6 parcours sur 6** passés, deux exécutions de suite (4,9 s et 4,8 s) | 6 sur 6 (complément, sans seuil dans la définition d'I5) | Atteint, sur une version plus ancienne (`sha-cd5751f`) | `frontend/e2e/resultats/journal-cluster.txt` (P7-05, 06/11/2026 10:00) ; non rejoués sur les digests de `22364bc` |

Aucun indicateur n'est hors seuil. Le relevé met en évidence de la dette qui ne dépasse aucun seuil mais dont la tendance est à surveiller (sections suivantes).

#### Limites de la mesure

Ce qui a changé depuis le relevé du 04/11/2026 :

- **I1** : la couverture est relevée à la fois dans la CI (pytest-cov, lignes et branches) et dans SonarCloud sur `main` (au 04/11, seule une pull request était analysée). Les deux sources diffèrent de quelques dixièmes de point (98,45 contre 98,5 pour catalog) : elles sont citées toutes les deux, aucune n'est recopiée de l'ancien relevé.
- **I2** : SonarCloud est relevé sur `main` après l'analyse de `22364bc`, avec 0 constat. La **complexité cognitive par fonction n'est toujours pas mesurée directement** (SonarCloud ne l'expose que par fichier) : la complexité cyclomatique de Ruff (C901) n'est qu'un indice. Le code des tests des services n'est pas contrôlé par `mypy --strict` en CI.
- **I3** : le seuil est mesuré avec **Locust sur le même Mac que le cluster k3d** (10 CPU partagés), à travers Traefik et TLS : le générateur de charge et les services se disputent le processeur, et aucun réseau réel n'est traversé. Le seuil vaut pour 50 utilisateurs ; le pic de 200 utilisateurs sert à franchir le seuil de l'HPA, ce n'est pas du trafic réel. Une seule exécution de référence par scénario : la variabilité entre exécutions n'est pas mesurée (la première exécution de P8-02, supprimée et remplacée après audit, avait donné 21 ms en lecture et 28 ms en publication ; la référence 21 et 23 ms : source, journal de la fiche P8-02).
- **I4** : le **front est maintenant scanné sur le digest publié, amd64 et arm64** (au 04/11, seul l'amd64 de l'image de la CI l'était). Les images des services restent scannées en **amd64 seulement**, avant publication : le job `publish` du backend n'a pas d'étape Trivy, donc l'arm64 des services n'est pas scanné. `--ignore-unfixed` écarte toujours les vulnérabilités sans correctif ; Trivy n'étant pas installé sur ce Mac, leur nombre n'a **pas** pu être mesuré (voir plus bas). Trivy 0.76.2 est la dernière version (publiée le 05/11/2026) ; la CI utilise toujours la 0.76.0.
- **I5** : les 17 tests tournent toujours sur une pile `docker compose`, pas sur le cluster. Les 6 parcours Playwright passent sur le cluster k3d (TLS mkcert vérifié) mais sur l'ancienne version `sha-cd5751f` et sans seuil formel : ils complètent I5, ils ne le remplacent pas.

#### Mesures nouvelles qui révèlent de la dette

Rien n'a été corrigé d'office, hormis un test d'une règle de validation (voir I1).

**I1 : lignes et branches non couvertes** (`uv run pytest --cov --cov-branch --cov-report=term-missing` dans chaque service, 06/11/2026, mêmes chiffres que la CI). On compte les **branches manquantes** (arcs), comme dans les pourcentages : `catalog-service` 8 lignes et 7 branches manquantes sur 120 (7 lignes partielles), `notification-service` 11 lignes et 8 branches manquantes sur 94 (6 lignes partielles).

| Service | Fichier : lignes ou branches | Contenu | Classe |
| --- | --- | --- | --- |
| catalog | `articles.py:58`, arc `57->58` | Frais de port supérieurs à 1 000 000 € refusés | **Règle de validation du code** (borne `MAX_PRICE`), **non spécifiée par RM-01** (« positifs ou nuls ») : **testée en phase 8** (voir ci-dessous) |
| catalog | `auth.py:91`, arcs `60->67` et `89->91` | Clé JWKS déjà en cache et valide : pas de rafraîchissement | Technique (cache JWKS) |
| catalog | `auth.py`, arc `131->130` | Clé JWKS ignorée quand `use` ou `kty` ne conviennent pas | Technique (filtrage des clés) |
| catalog | `correlation.py:41-42`, arcs `40->41` et `63->68` | Portée non HTTP transmise telle quelle ; erreur 500 après le début de la réponse | Technique (intergiciel) |
| catalog | `events.py:120-122` | Échec de la déclaration de l'exchange : la connexion est fermée avant de relancer l'erreur | Technique (chemin d'erreur d'infrastructure) |
| catalog | `persistence.py:18`, arc `17->18` | `IntegrityError` qui n'est pas un doublon : relancée telle quelle | Technique (chemin d'erreur) |
| notification | `auth.py:91`, arcs `60->67`, `89->91`, `131->130` | Identiques à catalog (fichier `auth.py` identique) | Technique |
| notification | `auth.py:210-212`, arcs `210->211` et `210->212` | `get_optional_user`, dépendance de routes publiques, **définie mais jamais utilisée** par ce service (recopiée avec le socle) | Technique (**code mort**) |
| notification | `correlation.py:41-42`, arcs `40->41` et `63->68` | Identiques à catalog | Technique |
| notification | `consumer.py:155-157` | Échec de la configuration de la file : la connexion est fermée | Technique (chemin d'erreur d'infrastructure) |
| notification | `consumer.py:169-170`, arc `115->120` | Échec de l'acquittement d'un message ; fermeture sans tâche en cours | Technique (chemin d'erreur d'infrastructure) |

Une seule ligne porte une règle de validation du code (et non une règle de gestion RM-01). Elle est maintenant testée (cas `1000000.00` accepté et `1000000.01` refusé, ajoutés dans `services/catalog-service/tests/test_articles_unit.py`) : **`catalog-service` passe de 8 à 7 lignes non couvertes et de 7 à 6 branches manquantes sur 120 (6 lignes partielles), de 289 à 291 tests** ; `ruff check`, `ruff format --check`, `mypy --strict src` et la couverture (≥ 80 %) passent. Ce test n'est pas dans le run 42219458020 (il est dans un commit postérieur) : les valeurs d'I1 du tableau ci-dessus sont celles du run, avant ce test. Le reste est technique.

**I2 : erreurs de `mypy --strict` sur les dossiers `tests/` des services** (`uv run mypy --strict src tests` dans chaque service, mypy 2.4.1 ; `tests` seul est évité car il produit du bruit d'imports non résolus (le paquet du service n'est alors pas trouvé) ; 06/11/2026 ; `tests/acceptance` : 0 erreur sur 8 fichiers). Ces 26 fichiers de tests ne sont pas contrôlés par la CI.

| Catégorie | catalog | notification | Total |
| --- | --- | --- | --- |
| `import-untyped` : bibliothèque `jsonschema` sans stubs | 2 | 1 | 3 |
| `arg-type` : clé `None` passée à `jwt.encode` (`test_security.py`, 2 par service) ; `PublishedEvent` mal typé (`test_events_unit.py`) | 2 | 6 | 8 |
| `comparison-overlap` : comparaison de tuples de flottants (`test_processing.py`) | 0 | 3 | 3 |
| `var-annotated` : annotation manquante (`test_api_articles.py`) | 1 | 0 | 1 |
| **Total** | **5** | **10** | **15** |

**I2 front : taille et complexité** (`npm run build`, comptages sur `src`, 06/11/2026) : le bundle JavaScript unique fait **609,4 Ko (184,1 Ko compressé)** et déclenche l'avertissement de Vite (> 500 Ko) ; 1 001 modules transformés ; 13 fichiers `.tsx` hors tests et 1 756 lignes de TypeScript hors tests ; le plus long fichier est `InterestsPage.tsx` (221 lignes) ; 11 fichiers de tests (62 tests passés). Aucune complexité n'est mesurée côté front : la chaîne n'a pas d'outil pour cela, et aucune dépendance n'a été ajoutée.

**I2 : duplication entre les services, invisible pour SonarCloud.** SonarCloud analyse un projet par service et mesure donc 0,0 % de duplication. Or le socle est recopié : `auth.py` (227 lignes), `correlation.py` (80), `errors.py` (140), `logging.py` (51) et `health.py` (33) sont **identiques** dans les deux services (comparaison après remplacement du nom du paquet), soit 531 lignes en double, **1 062 des 3 072 lignes de `src` (34,6 %)**. Un correctif de sécurité de `auth.py` doit être fait deux fois ; le code mort `get_optional_user` de notification en est une conséquence.

**I3 : marge de capacité.** À 200 utilisateurs (environ 87 requêtes par seconde), l'HPA monte à son **plafond de 5 réplicas** et la CPU moyenne reste à **72–75 %** de la requête (cible 70 %), soit environ 366m pour 5 × 100m demandés : le plafond est atteint vers 200 utilisateurs, sans marge au-delà. Les latences restent bonnes à 5 réplicas (p95 de 13 ms) : la limite est le plafond de l'HPA, pas un effondrement des performances (source : `protocole.md` de P8-03, paramètres et limites). Aucun essai au-delà de 200 utilisateurs n'a été fait.

**I4 : outillage et vulnérabilités écartées.**

- **Outillage du front** : `npm audit` (dépendances de développement comprises) signale **10 vulnérabilités modérées**, aucune HIGH ni CRITICAL, toutes dans la chaîne ESLint (`minimatch`, avis GHSA-g3hv-75wg-m249, et les paquets qui en dépendent : `eslint`, `@eslint/config-array`, `@eslint/js`, `@typescript-eslint/*`, `typescript-eslint`) ; npm propose `npm audit fix --force` et marque la correction comme changement majeur. Rien de tout cela n'est dans l'image.
- **Version de Trivy** : la CI utilise la **0.76.0** ; la dernière publiée est la **0.76.2** (05/11/2026, `gh api repos/aquasecurity/trivy/releases/latest`), soit deux versions de retard.
- **Vulnérabilités sans correctif** : **non mesurées**. Le scan sans `--ignore-unfixed` demande Trivy, absent de ce Mac ; l'installer ou lancer une image tierce n'est pas prévu par la tâche. Le nombre reste donc inconnu, et c'est le risque noté.

#### Axes d'amélioration contre la dette technique

| Indicateur | Écart ou risque constaté (avec son chiffre) | Action | Effet attendu sur la dette | Échéance ou statut |
| --- | --- | --- | --- | --- |
| I1 | 8 lignes et 7 branches manquantes sur 120 (catalog), 11 lignes et 8 branches manquantes sur 94 (notification) | **Fait en phase 8** : lignes et branches listées et classées ; la seule portant une règle de validation (frais de port > 1 000 000 €) est testée (catalog : 8 → 7 lignes, 7 → 6 branches manquantes). Les autres (7 lignes et 6 branches pour catalog, 11 et 8 pour notification) sont techniques (chemins d'erreur d'infrastructure, cache JWKS, code mort) : justifiées, non testées | Moins de risque de régression sur les bornes de validation ; le reste ne vaut pas le coût de simuler une panne d'infrastructure | Clos (P8-04) |
| I1 | Plafond de 1 000 000 € des frais de port (`MAX_PRICE`) : 1 règle de validation du code absente de RM-01 | Faire spécifier ce plafond par le Product Owner (RM-01) ou le retirer du code ; backlog inchangé en phase 8 | Une règle implicite devient soit une exigence testée, soit disparaît | Phase 9, à arbitrer |
| I1 | Le seuil de 80 % est très inférieur à la valeur mesurée (97,66 % au plus bas) : une baisse de 17 points passerait sans alerte du job `test` | Proposition : remonter `--cov-fail-under` à 95 % ; la quality gate SonarCloud contrôle déjà le code nouveau à 80 % | Une baisse de plus de 2,6 points devient bloquante | Phase 9, à arbitrer (l'ENF-22 fixe 80 %) |
| I2 | `mypy --strict` ne couvre pas les dossiers `tests/` : **15 erreurs** (5 catalog, 10 notification), 4 catégories | Corriger les 15 erreurs (annotations, clé de test typée, stubs `types-jsonschema` en dépendance de développement : à décider, car c'est une dépendance de plus), puis étendre l'étape `mypy` de `lint` aux tests | Typage contrôlé sur les 26 fichiers de tests des services en plus des 34 de `src` | **Replanifié en phase 9** : la phase 8 mesure sans corriger (périmètre de P8-04) ; effort estimé à environ une heure |
| I2 | Socle recopié dans les deux services : **531 lignes identiques ×2 (34,6 % des lignes de `src`)**, hors de portée de SonarCloud | Cible : paquet partagé pour `auth`, `correlation`, `errors`, `logging`, `health` ; pour le POC : un test qui compare les deux copies et échoue si elles divergent | Un seul endroit à corriger ; fin du code mort recopié (`get_optional_user` de notification, 3 lignes non couvertes) | Paquet partagé : cible (à ajouter à `architecture-cible.md`) ; test de comparaison : phase 9 si le temps le permet |
| I2 | Complexité cognitive par fonction non mesurée directement (indice : complexité cyclomatique maximale 10) | Garder la règle du profil Sonar way (seuil 15) ; relever à chaque revue le maximum de C901 de Ruff | Une fonction devenue illisible est repérée avant le seuil | Continu |
| I2 front | Bundle de **609 Ko** (184 Ko compressé) en un seul fichier, avertissement de Vite | Découper par page (`React.lazy` et `import()`) | Premier chargement allégé avant que MUI et les pages ne fassent grossir le bundle | Cible (le POC a 4 pages : gain faible) |
| I3 | Plafond de l'HPA atteint à environ 200 utilisateurs : 5 réplicas à 72–75 % de CPU (cible 70 %), sans marge | Relever `maxReplicas` (par exemple 8) dans les values du chart, ou la requête CPU (100m) après mesure, puis rejouer le pic | Marge au-delà de 200 utilisateurs ; le coût est la mémoire du Mac (8 Go alloués à Docker) | Cible : les ressources du Mac bornent le POC (limite déjà notée dans le protocole 5) |
| I3 | Une seule exécution de référence par scénario, sur le même Mac que le générateur de charge | Répéter l'exécution 3 fois et relever l'écart des p95 ; si possible, lancer Locust depuis une autre machine | Marge réelle (21 ms contre 300 ms) mieux établie ; une régression se distingue du bruit | Phase 9, si le temps le permet |
| I4 | **10 vulnérabilités modérées** dans l'outillage du front (chaîne ESLint) ; Trivy 0.76.0 alors que la 0.76.2 est sortie | Monter ESLint et `typescript-eslint` (essai en branche, correction marquée « majeure » par npm) ; monter Trivy en relevant la nouvelle somme SHA-256 | 0 vulnérabilité signalée par `npm audit` (outillage compris) ; scanner à jour | Phase 9 (plan de remédiation de sécurité) |
| I4 | Vulnérabilités sans correctif : nombre inconnu ; arm64 des services non scanné | Ajouter à la CI un scan complet sans `--ignore-unfixed`, non bloquant, dont le rapport est archivé ; ajouter au `publish` du backend l'étape « Trivy sur le digest publié (arm64) » que le front a déjà | Le plan de remédiation (critère 8) repose sur un décompte mesuré ; les deux architectures sont scannées | Phase 9 |
| I5 | 17 critères sur 17 en CI sur `docker compose`, 0 sur le cluster (action « Phase 6 » du relevé du 04/11) | **Clos** : décision du 05/11/2026 (journal des décisions) de ne pas créer de client Keycloak de test sur le cluster (un client à *Direct Access Grants* affaiblirait l'environnement qui joue la production) ; les mêmes images ont passé les 17 critères en CI, et les **6 parcours Playwright** (connexion PKCE réelle, TLS vérifié) vérifient le cluster à la place | Le cluster est vérifié par un vrai parcours utilisateur, sans compte de test à privilèges dans le cluster | Clos (P7-05 et P8-04) |
| I5 | 17 sur 17 en CI ; 6 parcours sur 6 sur le cluster en `sha-cd5751f`, non rejoués sur `22364bc` | Rejouer les 6 parcours sur le cluster au dernier tag, à la clôture de la phase 8 (`frontend/e2e/run-cluster.sh`), et noter le tag | La preuve couvre la version démontrée | Clôture de la phase 8 (chef) |

### Mesures du 04/11/2026 (phase 5, CI)

Relevé historique : les actions d'amélioration ci-dessous ont été reprises et mises à jour dans le relevé de la phase 8, qui est la référence.

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
| I2 SonarCloud, pull request n°2 (P5-06) | Les deux services : **0 code smell**, dette 0 min, 0 bug, 0 vulnérabilité, 0 hotspot, duplication 0,0 %, notes A, couverture 98,5 % et 97,6 % ; `api/issues/search?componentKeys=<clé>&pullRequest=2&resolved=false` renvoie `total: 0` | 0 constat | Atteint sur la pull request. Atteint sur la pull request | Run de la pull request [42045659784](https://github.com/Luucaaas/collector-poc/actions/runs/42045659784) (code final), relevé du 05/11/2026 |
| I2 SonarCloud, `main` après P5-06 | Les deux services : quality gate **OK**, **0 code smell** (contre 2 et 1 avant), dette **0 min** (contre 25 et 5 min), 0 bug, 0 vulnérabilité, 0 hotspot, duplication 0,0 %, notes A ; couverture 98,5 % (lignes 99,1, branches 94,2) et 97,6 % (98,4 / 91,1) | 0 constat, note A | **Atteint** | Run de `main` [42046581865](https://github.com/Luucaaas/collector-poc/actions/runs/42046581865) (commit `bec38ed`), API `measures/component` et `qualitygates/project_status` avec `&branch=main`, relevé du chef le 05/11/2026 15:43 |
| I1 couverture SonarCloud (lignes et branches) | `catalog-service` **98,5 %** (lignes 99,1 %, branches 94,5 %) ; `notification-service` **97,6 %** (lignes 98,4 %, branches 91,1 %) | ≥ 80 % | Atteint | Mêmes appels (`coverage`, `line_coverage`, `branch_coverage`). pytest-cov avec `branch = true` : 98,47 % et 97,60 % (run de la PR [42037655092](https://github.com/Luucaaas/collector-poc/actions/runs/42037655092)) |
| I4 vulnérabilités CRITICAL et HIGH avec correctif | **0** dans chaque image : `debian 13.7` et 41 paquets Python analysés, 0 vulnérabilité | 0 | Atteint | Tableau « Report Summary » de Trivy 0.76.0 dans `build-scan` |
| I4 secrets CRITICAL ou HIGH | **0** (colonne Secrets sans constat, code de sortie 0) | 0 | Atteint | Même journal |
| I4 front, dépendances embarquées | **0** vulnérabilité HIGH ou plus (`npm audit --omit=dev --audit-level=high`) ; 10 modérées dans l'outillage de développement (chaîne ESLint, `minimatch`), hors seuil | 0 | Atteint | Run [42184993666](https://github.com/Luucaaas/collector-poc/actions/runs/42184993666), journal du job `frontend`, relevé du 06/11/2026 |
| I4 front, image nginx | **0** vulnérabilité CRITICAL ou HIGH avec correctif (cible `alpine 3.24.2` du tableau « Report Summary » de Trivy 0.76.0), colonne Secrets sans constat (`-`), code de sortie 0, après `apk upgrade` ; avant, 1 CRITICAL et 7 HIGH sur la base officielle | 0 | Atteint | Même run ; run rouge [42184547804](https://github.com/Luucaaas/collector-poc/actions/runs/42184547804) pour l'état initial |
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
| I1 | Branches désormais mesurées (`branch = true`) : 94,5 % (catalog) et 91,1 % (notification) | Lister les branches partielles (`--cov-report=term-missing`) et tester celles qui portent une règle métier | Fait en phase 8 (P8-04), voir le relevé du 06/11/2026 |
| I1 | 8 lignes non couvertes (catalog) et 11 (notification) | Lister les lignes (`--cov-report=term-missing`), tester celles qui portent une règle métier, justifier les autres | Fait en phase 8 (P8-04), voir le relevé du 06/11/2026 |
| I1 | Le seuil de 80 % est très inférieur à la valeur mesurée (98 %) : il tolérerait une baisse de 18 points sans alerte | Fait en partie : la quality gate SonarCloud contrôle la couverture du code nouveau (≥ 80 %), blocage démontré (run 42037061364). Remonter le seuil global à 95 % reste possible | Clos (P5-04) |
| I2 | Duplication et complexité non vérifiées | Fait : job `sonar` (P5-04), duplication 0,0 % | Clos (P5-04) |
| I2 | Constats SonarCloud de `main` (première analyse complète, invisibles sur la pull request n°1) : 3 code smells, dette 30 min (catalog 2 : `python:S8414` BLOCKER et `python:S8786` MAJOR ; notification 1 : `python:S8414`) | Fait (P5-06, pull request n°2) : `CORSMiddleware` ajouté en dernier dans les deux services ; `_EMAIL` ancré sur l'arobase et `_is_national` en temps linéaire, avec un test de performance (pire cas de 100 000 caractères : 24 s avant, 2 ms après pour `_EMAIL`). Résultat sur la pull request : voir « Relevés ». Cycle mesure, axe, correction, nouvelle mesure | Clos (P5-06) |
| I2 | mypy strict ne couvre pas le code des tests des services | Étendre `mypy --strict` aux dossiers `tests/` des services, progressivement, ou documenter l'exclusion | Mesuré en phase 8 (15 erreurs) ; correction replanifiée en phase 9 |
| I4 | Base de vulnérabilités de Trivy non épinglée ; Trivy 0.76.0 n'est plus la dernière version ; arm64 non scanné ; vulnérabilités sans correctif invisibles | Mise à jour volontaire de Trivy (version, somme SHA-256) à chaque revue ; rapport complet sans `--ignore-unfixed` consigné au plan de remédiation ; scan de l'arm64 au `publish` en cible | Front : arm64 scanné depuis la fusion de P7-03 le 06/11 (`1702354`) ; reste en phase 9 pour les services et le rapport complet |
| I5 | Les tests ne tournent pas sur le cluster | Rejouer les 17 critères contre le cluster k3d avant la démonstration (déjà prévu dans la définition d'I5) | Clos en phase 8 : parcours Playwright à la place, voir le relevé du 06/11/2026 |

### Relevés de fin de sprint

Les cinq indicateurs ont été relevés sur une même version en phase 8 ; les valeurs sont reprises et mises à jour à chaque revue.

| Date | I1 | I2 | I3 | I4 | I5 | Commentaire |
| --- | --- | --- | --- | --- | --- | --- |
| 04/11/2026 | 99,06 % (catalog), 98,43 % (notification) | Ruff 0, mypy 0 ; SonarCloud : voir le relevé de la phase 5 (0 constat après P5-06) | Non mesuré (phase 8) | 0 CRITICAL ou HIGH, 0 secret | 17 sur 17 | Run 41825781085 (`main`, `49df273`) |
| 06/11/2026 | Lignes 99,06 % (catalog), 98,47 % (notification) ; branches 94,17 % et 91,49 % | Ruff 0, mypy 0 (15 erreurs hors CI dans les tests des services) ; SonarCloud : notes A, dette 0 min, duplication 0,0 %, 0 code smell ; ESLint 0 | p95 lecture 21 ms, publication 23 ms, 0 % de 5xx à 50 utilisateurs ; délai des notifications < 0,1 s | 0 CRITICAL ou HIGH, 0 secret ; `npm audit` 0 (10 modérées hors image) | 17 sur 17 ; 6 parcours Playwright sur 6 | Runs 42219458020 et 42219458005 (`main`, `22364bc`) ; I3 sur `sha-9d2c96e` (code identique). Voir « Mesures du 06/11/2026 (phase 8) » |
