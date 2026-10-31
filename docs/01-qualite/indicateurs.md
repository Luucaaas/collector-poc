# Indicateurs qualité

Cinq indicateurs mesurent la qualité du POC. Chacun est rattaché à une caractéristique de la norme ISO/IEC 25010:2023, a un seuil, un outil de mesure et une action en cas de dépassement. Les seuils reprennent **sans les modifier** les exigences non fonctionnelles de [exigences.md](../03-backlog/exigences.md) (ENF-05, 12, 13, 22, 23) et les critères d'acceptation de [user-stories.md](../03-backlog/user-stories.md).

Un indicateur n'est utile que s'il est mesuré à chaque modification, comparé à un seuil et suivi dans le temps. C'est ce suivi qui empêche l'accumulation de la dette technique : une dérive est visible dès le commit qui la crée, pas en fin de projet.

Les valeurs réelles sont relevées en phase 8 (section « Relevés »). Ce document ne contient aucune valeur mesurée.

## Synthèse

| # | Indicateur | Caractéristique ISO 25010 (sous-caractéristique) | Seuil | Outil | Moment de mesure | ENF liée |
| --- | --- | --- | --- | --- | --- | --- |
| I1 | Couverture de tests du code métier | Maintenabilité (testabilité) | ≥ 80 % | pytest-cov, SonarCloud | Chaque push et pull request (CI) | ENF-22 |
| I2 | Dette technique | Maintenabilité (analysabilité, modifiabilité) | Note de maintenabilité A ; duplication < 3 % ; complexité cognitive ≤ 15 par fonction ; Ruff et mypy sans erreur | SonarCloud, Ruff, mypy (mode strict) | Chaque push et pull request (CI) | ENF-23 |
| I3 | Latence p95 et taux d'erreur sous charge | Efficacité de performance (comportement temporel) ; Fiabilité (disponibilité) | Avec 50 utilisateurs Locust : p95 < 300 ms en lecture du catalogue, p95 < 500 ms en publication d'article, moins de 1 % de réponses 5xx | Locust, Prometheus, Grafana | Test de charge de la phase 8 et démo de disponibilité | ENF-12, ENF-13 |
| I4 | Vulnérabilités CRITICAL et HIGH | Sécurité (résistance) | 0 vulnérabilité CRITICAL ou HIGH avec correctif disponible ; 0 problème de sécurité bloquant SonarCloud | Trivy, SonarCloud | Chaque push et pull request (CI) | ENF-05 |
| I5 | Taux de critères d'acceptation validés | Adéquation fonctionnelle (complétude fonctionnelle, exactitude fonctionnelle) | 17 critères sur 17 passent | Tests d'acceptation pytest + httpx | CI et avant chaque démonstration | [user-stories.md](../03-backlog/user-stories.md) |

Outils du POC cités ici : ceux de la stack décidée (pytest, pytest-cov, SonarCloud, Ruff, mypy, Locust, Prometheus, Grafana, Trivy, pytest + httpx). Les versions exactes sont fixées dans les protocoles d'expérimentation (`docs/04-experimentations`).

## I1 — Couverture de tests du code métier

| Rubrique | Contenu |
| --- | --- |
| Caractéristique ISO 25010 | Maintenabilité, sous-caractéristique testabilité |
| Définition | Part des lignes (et des branches) du code métier exécutées par les tests automatisés |
| Formule | `lignes couvertes / lignes exécutables × 100`, calculée sur `services/*/src`, hors code de configuration et de démarrage |
| Seuil | ≥ 80 % (ENF-22) |
| Justification du seuil | Au-dessous, les règles de gestion (contrôle automatique, historique des prix, dédoublonnage des notifications) risquent de n'être vérifiées par aucun test. Au-dessus de 80 %, le gain marginal est faible pour un POC. |
| Outil | pytest-cov (mesure), SonarCloud (affichage et quality gate) |
| Où et quand | Étape « pytest + couverture » de la CI GitHub Actions, à chaque push et pull request. Rapport XML transmis à SonarCloud à l'étape suivante. |
| Qui suit | Lead Developer, à la revue de fin de sprint |
| Action si le seuil n'est pas respecté | La quality gate SonarCloud échoue et bloque le pipeline : aucune image n'est publiée sur GHCR. Les tests manquants sont écrits avant la fusion. |
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
| Où et quand | Ruff et mypy : première étape de la CI, bloquantes. SonarCloud : après les tests, quality gate bloquante. À chaque push et pull request. |
| Qui suit | Lead Developer, à la revue de fin de sprint |
| Action si le seuil n'est pas respecté | Ruff ou mypy en échec : le pipeline s'arrête avant les tests. Quality gate SonarCloud en échec : pas de publication d'image. Une dette acceptée volontairement est notée comme ticket de dette avec sa justification. |
| Effet sur la dette technique | C'est l'indicateur direct de la dette. La quality gate s'applique au code nouveau : chaque pull request ne peut pas aggraver la note, donc la dette ne s'accumule pas par petites touches. Le ratio suivi dans le temps montre la tendance. mypy strict évite les erreurs de type qui se paieraient plus tard en corrections. |

## I3 — Latence p95 et taux d'erreur sous charge

| Rubrique | Contenu |
| --- | --- |
| Caractéristique ISO 25010 | Efficacité de performance (comportement temporel) ; Fiabilité (disponibilité) |
| Définition | Latence au 95e percentile des requêtes de lecture du catalogue et de publication d'article, et part des réponses 5xx, sous charge nominale |
| Formules | p95 : durée en dessous de laquelle se terminent 95 % des requêtes du scénario ; taux d'erreur = `réponses 5xx / requêtes totales × 100` |
| Seuil | Avec 50 utilisateurs simultanés (Locust) : p95 < 300 ms en lecture du catalogue (ENF-12), p95 < 500 ms en publication d'article (ENF-12), moins de 1 % de réponses 5xx (ENF-13) |
| Justification du seuil | Une lecture du catalogue est une requête simple sur PostgreSQL : 300 ms laisse une marge confortable. La publication inclut le contrôle automatique et l'écriture de l'événement : 500 ms. Le p95 reflète l'expérience de la quasi-totalité des utilisateurs, contrairement à la moyenne. |
| Outils | Locust (génération de charge et statistiques), Prometheus (métriques `/metrics` des services), Grafana (tableau de bord : débit, latence p95, taux d'erreur) |
| Où et quand | Test de charge de la phase 8 sur le cluster k3d, rejoué lors de la démo de disponibilité (suppression d'un pod, montée de l'HPA). Résultats archivés dans `tests/load`. |
| Qui suit | Lead Developer |
| Action si le seuil n'est pas respecté | Ticket de dette ouvert avec la mesure, le scénario et l'hypothèse de cause (requête SQL, index, ressources du pod). Correction puis nouveau test avant la soutenance. |
| Effet sur la dette technique | La dette de performance est invisible tant qu'on ne mesure pas : une requête lente passe en revue sans alerte. Rejouer le même scénario Locust avec les mêmes seuils permet de comparer les relevés et de détecter une régression de latence introduite entre deux versions, avant qu'elle ne soit figée dans l'architecture. |

## I4 — Vulnérabilités CRITICAL et HIGH

| Rubrique | Contenu |
| --- | --- |
| Caractéristique ISO 25010 | Sécurité, sous-caractéristique résistance |
| Définition | Nombre de vulnérabilités connues de sévérité CRITICAL ou HIGH, avec correctif disponible, dans les dépendances et les images Docker, auquel s'ajoutent les problèmes de sécurité détectés par l'analyse statique SonarCloud |
| Formule | Décompte brut : `nombre de vulnérabilités CRITICAL + HIGH avec correctif` (Trivy) ; nombre de problèmes de sécurité ouverts à la quality gate (SonarCloud) |
| Seuil | 0 vulnérabilité CRITICAL ou HIGH avec correctif disponible, Trivy bloquant (ENF-05) |
| Justification du seuil | Une vulnérabilité sévère avec correctif disponible peut être supprimée sans coût fonctionnel : la tolérer est un choix, pas une contrainte. Celles sans correctif sont consignées dans le plan de remédiation, car aucune action immédiate n'est possible. |
| Outils | Trivy (dépendances, image, secrets), SonarCloud (analyse statique du code) |
| Où et quand | Étape Trivy de la CI, après le build Docker et avant le push sur GHCR, à chaque push et pull request |
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
| Où et quand | Exécutés en CI contre l'environnement de test, et avant chaque démonstration contre le cluster local |
| Qui suit | Lead Developer |
| Action si le seuil n'est pas respecté | Le test en échec bloque la fusion. Soit le code est corrigé, soit le critère est révisé dans le backlog avec une décision documentée. |
| Effet sur la dette technique | Le nom des tests relie chaque critère à une preuve exécutable. Si un refactoring ou une montée de version casse un comportement métier, le critère correspondant échoue immédiatement. La dette fonctionnelle (écart entre backlog et code) ne peut donc pas s'installer en silence. |

## Suivi dans le temps

| Indicateur | Où voir la valeur | Fréquence |
| --- | --- | --- |
| I1, I2 | Tableau de bord du projet SonarCloud (historique, tendance du ratio de dette) | À chaque analyse CI |
| I4 | Journal de l'étape Trivy dans les artefacts de la CI ; SonarCloud pour l'analyse statique | À chaque exécution du pipeline |
| I5 | Rapport pytest dans les artefacts de la CI | À chaque exécution du pipeline |
| I3 | Grafana pendant le test de charge ; résultats Locust archivés dans `tests/load` | À chaque campagne de charge (phase 8) |

Revue de fin de sprint : le Lead Developer relève les cinq valeurs, les compare aux seuils, inscrit le résultat dans la section « Relevés » et ouvre un ticket de dette pour chaque indicateur hors seuil, avec une échéance.

## Relevés

Rempli en phase 8.

| Date | I1 | I2 | I3 | I4 | I5 | Commentaire |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |
