# Backlog du POC

Cinq user stories couvrent la fonctionnalité métier du POC : **un vendeur publie un article ou modifie son prix, le contrôle automatique tranche, puis un événement déclenche la notification des acheteurs intéressés.**

Les identifiants EF, ENF et RM renvoient à [exigences.md](exigences.md). Chaque critère d'acceptation devient un test d'acceptation pytest (client httpx) dans [`tests/acceptance/`](../../tests/acceptance/), nommé d'après la story et le critère : `test_us03_ca2_article_avec_coordonnees_rejete`.

## Vue d'ensemble

| ID | Story | Priorité | Points | Critères | Exigences couvertes |
| --- | --- | --- | --- | --- | --- |
| US-01 | Admin : créer une catégorie | Must | 2 | 3 | EF-09, EF-27, RM-06 |
| US-02 | Vendeur : créer une boutique | Must | 2 | 3 | EF-02, EF-05, EF-09, RM-02, RM-05 |
| US-03 | Vendeur : publier un article (contrôle automatique) | Must | 5 | 4 | EF-01, EF-03, EF-04, EF-05, RM-01 à RM-03 |
| US-04 | Vendeur : modifier le prix d'un article (historique conservé) | Must | 3 | 3 | EF-06, RM-04, ENF-08 |
| US-05 | Acheteur : définir ses centres d'intérêt et préférences, recevoir les notifications | Must | 5 | 4 | EF-10, EF-12 à EF-16, RM-08, ENF-14 |
| | **Total** | | **17** | **17** | |

Chaque story vérifie aussi ENF-02 (authentification), ENF-03 (autorisation) et ENF-07 (validation des entrées) par ses critères d'erreur 401, 403 et 422. Les jetons expirés ou falsifiés sont couverts par les tests unitaires de chaque service.

**Priorisation MoSCoW.** Les cinq stories sont en *Must* : elles forment la chaîne minimale qui démontre la fonctionnalité de bout en bout. Sans catégorie ni boutique, pas d'article. Sans article, pas d'événement. Sans centres d'intérêt, pas de notification. La consultation des alertes de fraude (ancienne US-06) est sortie du POC (ADR 0007).

**Estimation.** Points de complexité relative sur la suite de Fibonacci. La référence est US-01 (2 points : un endpoint protégé, sans événement). US-03 et US-05 valent 5, car elles combinent règles métier, émission ou consommation d'un événement et un test qui traverse les deux services.

**Ordre de réalisation.** US-01 → US-02 → US-03 → US-04 → US-05.

### Comptes de démonstration

Les critères utilisent des comptes provisionnés dans le realm Keycloak `collector`, importé depuis un fichier JSON :

| Compte | Rôles | Usage |
| --- | --- | --- |
| `admin` | `admin` | Catégories |
| `alice` | `seller`, `buyer` | Vendeur principal (compte qui cumule deux rôles) |
| `bob` | `seller` | Second vendeur, pour les contrôles de propriété |
| `chloe` | `buyer` | Acheteur |

### Définition de prêt (DoR) et définition de terminé (DoD)

- **Prête** : la story a ses critères d'acceptation, ses exigences liées et son estimation. Les endpoints et événements qu'elle utilise sont décrits dans `docs/02-architecture/contrats.md`.
- **Terminée** : les tests d'acceptation de la story passent en CI. La couverture du service reste ≥ 80 %. La quality gate SonarCloud et le scan Trivy sont au vert. L'OpenAPI est à jour. Le service est déployé sur le cluster par `deploy/local/deploy.sh`.

### Exigences transverses sans story dédiée

| Exigence | Où elle est garantie |
| --- | --- |
| EF-08 Inscription obligatoire | Configuration du realm Keycloak (ADR 0004). Toutes les écritures exigent un jeton, comme le vérifient les critères 401 de chaque story |
| EF-25 et EF-35 Outil anti-fraude interne ou acheté, évolutivité | Exchange `article.events` de type `topic` : un nouveau consommateur s'abonne avec sa propre file, sans modifier `catalog-service`. Démontré pendant la soutenance en liant une file supplémentaire (ADR 0001) |
| ENF-18 Livraison des événements | Message persistant, file durable et acquittement après traitement, vérifiés par les tests d'intégration de `notification-service` |

---

## US-01 — Créer une catégorie

**En tant qu'** administrateur, **je veux** créer une catégorie d'objets de collection **afin que** les vendeurs y classent leurs articles et que les acheteurs s'y abonnent.

- Priorité : Must · Estimation : 2 points
- Exigences : EF-27, EF-09, RM-06

| # | Critère d'acceptation |
| --- | --- |
| CA1 | **Étant donné** que je suis authentifié comme `admin`, **quand** je crée la catégorie « Figurines Star Wars », **alors** la réponse est 201 avec le slug `figurines-star-wars`, et la catégorie apparaît dans la liste publique des catégories, consultable sans authentification. |
| CA2 | **Étant donné** que la catégorie « Baskets » existe, **quand** l'admin crée « baskets » (doublon, sans tenir compte de la casse) ou une catégorie dont le nom fait 1 caractère, **alors** la réponse est respectivement 409 ou 422, et aucune catégorie n'est créée. |
| CA3 | **Étant donné** que j'appelle l'API sans jeton, ou authentifié comme `bob` (seul rôle `seller`), **quand** je crée une catégorie, **alors** la réponse est respectivement 401 ou 403. |

## US-02 — Créer une boutique

**En tant que** vendeur, **je veux** créer une ou plusieurs boutiques virtuelles **afin de** regrouper mes articles par thème, en étant clairement identifié comme vendeur particulier.

- Priorité : Must · Estimation : 2 points
- Exigences : EF-02, EF-05, EF-09, RM-02, RM-05

| # | Critère d'acceptation |
| --- | --- |
| CA1 | **Étant donné** que le compte `alice` (rôle `seller`) est authentifié, **quand** `alice` crée la boutique « Jouets des années 80 », **alors** la réponse est 201, la boutique appartient à `alice`, porte le type de vendeur `INDIVIDUAL`, et sa page publique est consultable sans authentification. |
| CA2 | **Étant donné** que `alice` est authentifié comme vendeur, **quand** `alice` crée une boutique dont la description contient une adresse email ou un numéro de téléphone, **alors** la réponse est 422 avec le motif `CONTACT_EMAIL` ou `CONTACT_PHONE`, et aucune boutique n'est créée. |
| CA3 | **Étant donné** que j'appelle l'API sans jeton, ou authentifié comme `chloe` (seul rôle `buyer`), **quand** je crée une boutique, **alors** la réponse est respectivement 401 ou 403. |

## US-03 — Publier un article

**En tant que** vendeur, **je veux** publier un article dans l'une de mes boutiques et qu'il soit contrôlé automatiquement **afin qu'**il soit mis en vente sans attendre une validation humaine.

- Priorité : Must · Estimation : 5 points
- Exigences : EF-01, EF-03, EF-04, EF-05, RM-01, RM-02, RM-03

| # | Critère d'acceptation |
| --- | --- |
| CA1 | **Étant donné** qu'`alice` possède une boutique et que la catégorie « Figurines » existe, **quand** `alice` publie un article conforme (titre, description, photo, prix de 120 €, frais de port de 8 €), **alors** la réponse est 201 avec le statut `PUBLISHED`, un événement `article.published` est publié sur l'exchange `article.events`, et l'article apparaît dans le catalogue public filtré sur « Figurines ». |
| CA2 | **Étant donné** qu'`alice` possède une boutique, **quand** `alice` publie un article dont la description contient une adresse email ou un numéro de téléphone (`06 12 34 56 78`, `+33 6 12 34 56 78`), **alors** la réponse est 201 avec le statut `REJECTED` et le motif `CONTACT_EMAIL` ou `CONTACT_PHONE`, aucun événement n'est publié, et l'article n'apparaît pas dans le catalogue public. |
| CA3 | **Étant donné** qu'`alice` possède une boutique, **quand** `alice` envoie un article invalide (prix nul ou négatif, aucune photo, catégorie inexistante), **alors** la réponse est 422 et aucun article n'est enregistré. |
| CA4 | **Étant donné** que `bob` possède une boutique, **quand** `alice` publie dans la boutique de `bob`, que `chloe` (seul rôle `buyer`) publie, ou qu'un appel arrive sans jeton, **alors** la réponse est respectivement 403, 403 ou 401. |

## US-04 — Modifier le prix d'un article

**En tant que** vendeur, **je veux** modifier le prix d'un de mes articles publiés **afin d'**ajuster mon offre au marché, tout en gardant l'historique des prix.

- Priorité : Must · Estimation : 3 points
- Exigences : EF-06, RM-04, ENF-08

| # | Critère d'acceptation |
| --- | --- |
| CA1 | **Étant donné** qu'`alice` a publié un article à 120 €, **quand** `alice` passe son prix à 95 €, **alors** la réponse est 200 avec le prix de 95 €, l'historique contient une entrée 120 € → 95 € datée et attribuée à `alice`, et un événement `article.price_changed` est publié avec l'ancien et le nouveau prix. |
| CA2 | **Étant donné** qu'`alice` a publié un article à 120 €, **quand** `alice` saisit un prix invalide (0 ou -10), **alors** la réponse est 422 et le prix reste à 120 €. |
| CA3 | **Étant donné** qu'`alice` a publié un article à 120 €, **quand** `bob` modifie son prix, ou qu'un appel arrive sans jeton, **alors** la réponse est respectivement 403 ou 401, et le prix reste à 120 €. |

## US-05 — Centres d'intérêt, préférences et notifications

**En tant qu'** acheteur, **je veux** déclarer mes centres d'intérêt et choisir les notifications que je reçois **afin d'**être prévenu des nouveaux articles et des changements de prix qui m'intéressent.

- Priorité : Must · Estimation : 5 points
- Exigences : EF-10, EF-12, EF-13, EF-14, EF-15, EF-16, RM-08, ENF-14

| # | Critère d'acceptation |
| --- | --- |
| CA1 | **Étant donné** que le compte `chloe` (rôle `buyer`) est authentifié, **quand** `chloe` déclare « Baskets » et « Figurines » comme centres d'intérêt et désactive les notifications de changement de prix, **alors** les deux réponses sont 200 et la relecture renvoie ces deux catégories et ces préférences. |
| CA2 | **Étant donné** que `chloe` s'intéresse à « Figurines » avec les notifications « nouvel article » activées, **quand** `alice` publie un article conforme dans « Figurines », **alors** en moins de 2 secondes une notification `NEW_ARTICLE` portant le titre et le prix de l'article apparaît dans les notifications de `chloe`, et `alice` ne reçoit aucune notification pour son propre article. |
| CA3 | **Étant donné** que `chloe` s'intéresse à « Figurines », **quand** `alice` passe le prix d'un article de cette catégorie de 120 € à 95 €, **alors** `chloe` reçoit une notification `PRICE_CHANGED` indiquant 120 € → 95 € si ce type est activé, et aucune s'il est désactivé. |
| CA4 | **Étant donné** que `chloe` a des notifications, **quand** un appel arrive sans jeton ou authentifié comme `bob` (seul rôle `seller`), **alors** la réponse est respectivement 401 ou 403. `alice`, qui a le rôle `buyer`, ne voit que ses propres notifications. |
