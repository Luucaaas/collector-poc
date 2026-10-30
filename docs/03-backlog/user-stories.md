# Backlog du POC

Six user stories couvrent la fonctionnalité métier du POC : **un vendeur publie un article ou modifie son prix, le contrôle automatique tranche, puis les événements déclenchent les notifications des acheteurs et l'analyse anti-fraude.**

Les identifiants EF, ENF et RM renvoient à [exigences.md](exigences.md). Chaque critère d'acceptation existe aussi en Gherkin dans [`tests/acceptance/features/`](../../tests/acceptance/features/), où il est exécuté par pytest-bdd.

## Vue d'ensemble

| ID | Story | Priorité | Points | Exigences couvertes |
| --- | --- | --- | --- | --- |
| US-01 | Admin : créer une catégorie | Must | 2 | EF-09, EF-27, RM-06 |
| US-02 | Vendeur : créer une boutique | Must | 3 | EF-02, EF-05, EF-09, RM-02, RM-05 |
| US-03 | Vendeur : publier un article (contrôle automatique) | Must | 8 | EF-01, EF-03, EF-04, EF-05, EF-23, RM-01 à RM-03, ENF-18 |
| US-04 | Vendeur : modifier le prix d'un article (historique conservé) | Must | 5 | EF-06, EF-23, RM-04, ENF-08 |
| US-05 | Acheteur : définir ses centres d'intérêt et préférences, recevoir les notifications | Must | 8 | EF-10, EF-12 à EF-16, RM-08, RM-09, ENF-14, ENF-19 |
| US-06 | Admin : consulter et traiter les alertes de fraude | Should | 5 | EF-24, EF-25, EF-26, RM-07, RM-09 |
| | **Total** | | **31** | |

Toutes les stories couvrent aussi ENF-02 (authentification), ENF-03 (autorisation) et ENF-07 (validation des entrées), vérifiées par les critères d'erreur 401, 403 et 422.

**Priorisation MoSCoW.** Les stories 1 à 5 forment la chaîne minimale qui démontre la fonctionnalité de bout en bout : sans catégorie ni boutique, aucun article ; sans article, aucun événement. US-06 est en *Should* : le service anti-fraude détecte et enregistre les alertes dès US-03 et US-04 (EF-23, EF-24), seule leur consultation par l'admin peut être reportée sans casser la chaîne.

**Estimation.** Points de complexité relative sur la suite de Fibonacci. La référence est US-01 (2 points : un endpoint CRUD protégé, sans événement). US-03 et US-05 valent 8 car elles combinent règles métier, émission ou consommation d'événements et tests d'intégration avec le broker.

**Ordre de réalisation.** US-01 → US-02 → US-03 → US-04, puis US-05 et US-06 en parallèle, car elles ne dépendent que des événements émis par US-03 et US-04.

### Comptes de démonstration

Les critères utilisent des comptes provisionnés dans le realm Keycloak `collector` :

| Compte | Rôles | Usage |
| --- | --- | --- |
| `admin` | `admin` | Catégories, alertes de fraude |
| `alice` | `seller`, `buyer` | Vendeur principal (compte qui cumule deux rôles) |
| `bob` | `seller` | Second vendeur, pour les contrôles de propriété |
| `chloe` | `buyer` | Acheteur |

### Définition de prêt (DoR) et définition de terminé (DoD)

- **Prête** : la story a ses critères d'acceptation, ses exigences liées et son estimation. Les contrats d'API et d'événements qu'elle utilise sont décrits dans `docs/02-architecture/contrats.md`.
- **Terminée** : tous les scénarios Gherkin de la story passent en CI. La couverture du service reste ≥ 80 %. La quality gate SonarCloud et les scans de sécurité sont au vert. L'OpenAPI est à jour. Les écrans de la story sont traduits en français et en anglais, et passent le contrôle d'accessibilité axe. Le service est déployé sur le cluster par Argo CD.

### Exigences transverses sans story dédiée

Quatre exigences du périmètre POC ne correspondent pas à une fonctionnalité isolée. Elles sont garanties par la DoD ou par l'architecture :

| Exigence | Où elle est garantie |
| --- | --- |
| EF-08 Inscription obligatoire | Configuration du realm Keycloak (ADR 0004). Toutes les écritures exigent un jeton, comme le vérifient les critères 401 de chaque story |
| EF-33 Internationalisation | DoD : écrans traduits en français et en anglais (react-i18next) |
| EF-34 Accessibilité | DoD : contrôle axe dans les tests Playwright (ENF-25) |
| EF-35 Évolutivité fonctionnelle | Architecture orientée événements (ADR 0001), démontrée par les deux consommateurs indépendants de US-05 et US-06 |

---

## US-01 — Créer une catégorie

**En tant qu'** administrateur, **je veux** créer une catégorie d'objets de collection **afin que** les vendeurs y classent leurs articles et que les acheteurs s'y abonnent.

- Priorité : Must · Estimation : 2 points
- Exigences : EF-27, EF-09, RM-06
- Gherkin : [`us01_creer_categorie.feature`](../../tests/acceptance/features/us01_creer_categorie.feature)

| # | Critère d'acceptation |
| --- | --- |
| 1 | **Étant donné** que je suis authentifié avec le rôle `admin`, **quand** je crée la catégorie « Figurines Star Wars », **alors** la réponse est 201 avec l'identifiant et le slug `figurines-star-wars`, et la catégorie apparaît dans la liste publique des catégories, consultable sans authentification. |
| 2 | **Étant donné** que la catégorie « Baskets » existe, **quand** je crée la catégorie « baskets », **alors** la réponse est 409 (nom déjà utilisé, sans tenir compte de la casse). |
| 3 | **Étant donné** que je suis administrateur, **quand** je crée une catégorie dont le nom fait 1 caractère, **alors** la réponse est 422 et aucune catégorie n'est créée. |
| 4 | **Étant donné** que je ne suis pas authentifié, **quand** je crée une catégorie, **alors** la réponse est 401. |
| 5 | **Étant donné** que je suis authentifié avec le seul rôle `seller`, **quand** je crée une catégorie, **alors** la réponse est 403. |

## US-02 — Créer une boutique

**En tant que** vendeur, **je veux** créer une ou plusieurs boutiques virtuelles **afin de** regrouper mes articles par thème, en étant clairement identifié comme vendeur particulier.

- Priorité : Must · Estimation : 3 points
- Exigences : EF-02, EF-05, EF-09, RM-02, RM-05
- Gherkin : [`us02_creer_boutique.feature`](../../tests/acceptance/features/us02_creer_boutique.feature)

| # | Critère d'acceptation |
| --- | --- |
| 1 | **Étant donné** que le compte `alice` (rôle `seller`) est authentifié, **quand** `alice` crée la boutique « Jouets des années 80 », **alors** la réponse est 201, la boutique appartient à `alice` et porte le type de vendeur `INDIVIDUAL`. |
| 2 | **Étant donné** que la boutique d'`alice` existe, **quand** un visiteur non authentifié consulte sa page publique, **alors** la réponse est 200 et la boutique est présentée comme tenue par un vendeur particulier. |
| 3 | **Étant donné** qu'`alice` possède déjà une boutique, **quand** `alice` en crée une seconde, **alors** la réponse est 201 et la liste de ses boutiques en contient deux. |
| 4 | **Étant donné** que la boutique « Jouets des années 80 » existe, **quand** `bob` crée la boutique « jouets des années 80 », **alors** la réponse est 409. |
| 5 | **Étant donné** que je suis authentifié avec le rôle `seller`, **quand** je crée une boutique dont la description contient une adresse email ou un numéro de téléphone, **alors** la réponse est 422 avec le motif `CONTACT_INFO_FORBIDDEN` et aucune boutique n'est créée. |
| 6 | **Étant donné** que je ne suis pas authentifié, ou que je n'ai que le rôle `buyer`, **quand** je crée une boutique, **alors** la réponse est respectivement 401 ou 403. |

## US-03 — Publier un article

**En tant que** vendeur, **je veux** publier un article dans l'une de mes boutiques et qu'il soit contrôlé automatiquement **afin qu'**il soit mis en vente sans attendre une validation humaine.

- Priorité : Must · Estimation : 8 points
- Exigences : EF-01, EF-03, EF-04, EF-05, EF-23, RM-01, RM-02, RM-03, ENF-18
- Gherkin : [`us03_publier_article.feature`](../../tests/acceptance/features/us03_publier_article.feature)

| # | Critère d'acceptation |
| --- | --- |
| 1 | **Étant donné** qu'`alice` possède une boutique et que la catégorie « Figurines » existe, **quand** `alice` publie un article conforme (titre, description, photo, prix de 120 €, frais de port de 8 €), **alors** la réponse est 201 avec le statut `PUBLISHED`, un seul événement `article.published` est émis, et l'article apparaît dans le catalogue public filtré sur « Figurines », consultable sans authentification. |
| 2 | **Étant donné** qu'`alice` possède une boutique, **quand** `alice` publie un article dont la description contient une adresse email, **alors** la réponse est 201 avec le statut `REJECTED` et le motif `CONTACT_EMAIL`, aucun événement n'est émis, et l'article n'apparaît pas dans le catalogue public. |
| 3 | **Étant donné** qu'`alice` possède une boutique, **quand** `alice` publie un article dont la description contient un numéro de téléphone, quel que soit son format (`06 12 34 56 78`, `+33 6 12 34 56 78`, `06.12.34.56.78`), **alors** l'article est `REJECTED` avec le motif `CONTACT_PHONE`. |
| 4 | **Étant donné** qu'`alice` possède une boutique, **quand** `alice` envoie un article invalide (prix nul ou négatif, aucune photo, titre trop court, catégorie inexistante), **alors** la réponse est 422 et aucun article n'est enregistré. |
| 5 | **Étant donné** que `bob` possède une boutique, **quand** `alice` publie un article dans la boutique de `bob`, **alors** la réponse est 403. |
| 6 | **Étant donné** que je ne suis pas authentifié, ou que je n'ai que le rôle `buyer`, **quand** je publie un article, **alors** la réponse est respectivement 401 ou 403. |

## US-04 — Modifier le prix d'un article

**En tant que** vendeur, **je veux** modifier le prix d'un de mes articles publiés **afin d'**ajuster mon offre au marché, tout en gardant l'historique des prix.

- Priorité : Must · Estimation : 5 points
- Exigences : EF-06, EF-23, RM-04, ENF-08
- Gherkin : [`us04_modifier_prix.feature`](../../tests/acceptance/features/us04_modifier_prix.feature)

| # | Critère d'acceptation |
| --- | --- |
| 1 | **Étant donné** qu'`alice` a publié un article à 120 €, **quand** `alice` passe son prix à 95 €, **alors** la réponse est 200 avec le prix de 95 €, l'historique contient une entrée 120 € → 95 € datée et attribuée à `alice`, et un événement `article.price_changed` est émis avec l'ancien et le nouveau prix. |
| 2 | **Étant donné** qu'`alice` a publié un article à 120 €, **quand** `alice` saisit de nouveau 120 €, **alors** la réponse est 200, l'historique ne change pas et aucun événement n'est émis. |
| 3 | **Étant donné** qu'`alice` a publié un article à 120 €, **quand** `alice` saisit un prix invalide (0, -10 ou 1,234), **alors** la réponse est 422 et le prix reste à 120 €. |
| 4 | **Étant donné** qu'`alice` a publié un article à 120 €, **quand** un visiteur non authentifié ou `bob` modifie son prix, **alors** la réponse est respectivement 401 ou 403, et le prix reste à 120 €. |
| 5 | **Étant donné** que l'article d'`alice` est au statut `REJECTED`, **quand** `alice` modifie son prix, **alors** la réponse est 409. |
| 6 | **Étant donné** qu'`alice` a modifié trois fois le prix de son article, **quand** `alice` consulte l'historique des prix, **alors** `alice` obtient trois entrées dans l'ordre chronologique. |

## US-05 — Centres d'intérêt, préférences et notifications

**En tant qu'** acheteur, **je veux** déclarer mes centres d'intérêt, suivre des articles et choisir les notifications que je reçois **afin d'**être prévenu des nouveaux articles et des baisses de prix qui m'intéressent.

- Priorité : Must · Estimation : 8 points
- Exigences : EF-10, EF-12, EF-13, EF-14, EF-15, EF-16, RM-08, RM-09, ENF-14, ENF-19
- Gherkin : [`us05_notifications_acheteur.feature`](../../tests/acceptance/features/us05_notifications_acheteur.feature)

| # | Critère d'acceptation |
| --- | --- |
| 1 | **Étant donné** que le compte `chloe` (rôle `buyer`) est authentifié, **quand** `chloe` déclare « Baskets » et « Figurines » comme centres d'intérêt, **alors** la réponse est 200 et ses centres d'intérêt contiennent ces deux catégories. |
| 2 | **Étant donné** que `chloe` s'intéresse à « Figurines » avec les notifications « nouvel article » activées, **quand** `alice` publie un article conforme dans « Figurines », **alors** en moins de 2 secondes une notification `NEW_ARTICLE` portant le titre et le prix de l'article apparaît dans les notifications de `chloe`, et `alice` ne reçoit aucune notification pour son propre article. |
| 3 | **Étant donné** que `chloe` suit un article à 120 €, **quand** `alice` passe son prix à 95 €, **alors** une notification `PRICE_CHANGED` indiquant 120 € → 95 € apparaît dans les notifications de `chloe`. |
| 4 | **Étant donné** que `chloe` suit un article et a désactivé les notifications « changement de prix », **quand** le prix de l'article change, **alors** `chloe` ne reçoit aucune notification. |
| 5 | **Étant donné** que `chloe` s'intéresse à « Figurines », **quand** le même événement `article.published` est livré deux fois, **alors** `chloe` ne reçoit qu'une seule notification. |
| 6 | **Étant donné** que `chloe` a des notifications, **quand** un visiteur non authentifié ou `alice` consulte les notifications, **alors** le visiteur reçoit 401 et `alice` ne voit que les siennes, jamais celles de `chloe`. |

## US-06 — Consulter et traiter les alertes de fraude

**En tant qu'** administrateur, **je veux** consulter les alertes produites par l'analyse anti-fraude et statuer sur chacune **afin de** repérer les prix anormaux et les vendeurs suspects avant qu'ils ne lèsent des acheteurs.

- Priorité : Should · Estimation : 5 points
- Exigences : EF-24, EF-25, EF-26, RM-07, RM-09
- Gherkin : [`us06_alertes_fraude.feature`](../../tests/acceptance/features/us06_alertes_fraude.feature)

| # | Critère d'acceptation |
| --- | --- |
| 1 | **Étant donné** que le plafond de prix est de 10 000 €, **quand** `alice` publie un article à 15 000 €, **alors** une alerte `PRICE_ABOVE_CEILING` liée à cet article et à `alice` apparaît dans la liste des alertes consultée par l'admin. |
| 2 | **Étant donné** qu'`alice` a publié un article à 100 €, **quand** `alice` passe son prix à 180 € (hausse de 80 %), **alors** une alerte `PRICE_SPIKE` est créée. Une hausse à 140 € (40 %) n'en crée aucune. |
| 3 | **Étant donné** qu'`alice` a modifié 3 fois le prix d'un article dans les dernières 24 h, **quand** `alice` le modifie une quatrième fois, **alors** une alerte `FREQUENT_PRICE_CHANGES` est créée. |
| 4 | **Étant donné** qu'une alerte est au statut `OPEN`, **quand** l'admin la marque `CONFIRMED` ou `DISMISSED`, **alors** la réponse est 200 et le nouveau statut est conservé. |
| 5 | **Étant donné** que le même événement déclencheur est livré deux fois, **quand** le service anti-fraude le traite, **alors** une seule alerte est créée. |
| 6 | **Étant donné** que je ne suis pas authentifié, ou que je suis `alice` (rôles `seller` et `buyer`), **quand** je consulte les alertes, **alors** la réponse est respectivement 401 ou 403. |
