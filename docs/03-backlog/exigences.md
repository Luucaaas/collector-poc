# Exigences de Collector.shop

Ce document reformule les exigences du contexte Collector.shop (V1 du 04/03/2025) et les complète là où le sujet l'autorise. Chaque exigence porte un identifiant stable, réutilisé dans le backlog, les contrats d'API, les tests d'acceptation et les ADR.

**Périmètre** :
- **POC** : implémenté et testé dans le prototype.
- **POC partiel** : le POC en réalise une partie, précisée dans la colonne « Remarque ».
- **Cible** : prévu dans l'architecture cible uniquement, non implémenté.

## 1. Acteurs

| Acteur | Description | Rôle Keycloak |
| --- | --- | --- |
| Visiteur | Internaute non authentifié. Parcourt le catalogue. | aucun |
| Acheteur | Particulier inscrit qui achète des objets, suit des articles et reçoit des notifications. | `buyer` |
| Vendeur | Particulier inscrit qui ouvre des boutiques et publie des articles. Un même compte peut cumuler `buyer` et `seller`. | `seller` |
| Administrateur | Employé de Collector qui gère le back-office : catégories, modération, alertes de fraude. | `admin` |
| Outil anti-fraude | Composant interne ou produit acheté, qui consomme les événements du catalogue. | compte de service |

## 2. Exigences fonctionnelles

### 2.1 Catalogue

| ID | Exigence | Périmètre | Remarque |
| --- | --- | --- | --- |
| EF-01 | Un visiteur parcourt le catalogue des articles publiés sans être authentifié, et le filtre par catégorie. | POC | Recherche plein texte et tri : cible |
| EF-02 | Un vendeur crée une ou plusieurs boutiques virtuelles. Chaque boutique l'identifie clairement comme **vendeur particulier**. | POC | |
| EF-03 | Un vendeur publie un article dans l'une de ses boutiques avec un titre, une description précise, au moins une photo, un prix et des frais de port. | POC partiel | Photos référencées par URL dans le POC. Téléversement et stockage objet : cible |
| EF-04 | Un article n'est mis en vente qu'après un contrôle de Collector, automatisé au maximum pour éviter l'intervention humaine. | POC | Règles RM-01 à RM-03 |
| EF-05 | Le système empêche l'échange de données personnelles (adresse email, numéro de téléphone) dans les textes publiés, afin d'interdire les transactions hors plateforme. | POC partiel | Appliqué aux articles et aux boutiques dans le POC. Chat : cible (EF-21) |
| EF-06 | Un vendeur modifie le prix d'un de ses articles. Chaque variation est collectée et historisée (ancien prix, nouveau prix, date, auteur). | POC | |
| EF-07 | Le catalogue présente les articles d'un vendeur et ses boutiques. | Cible | |

### 2.2 Comptes et rôles

| ID | Exigence | Périmètre | Remarque |
| --- | --- | --- | --- |
| EF-08 | L'inscription est obligatoire pour acheter ou vendre. | POC partiel | Comptes gérés par Keycloak. Le POC utilise des comptes de démonstration provisionnés dans le realm. L'inscription en libre-service est une option du realm, activable sans code |
| EF-09 | La plateforme distingue trois rôles : acheteur, vendeur et administrateur. Un utilisateur peut être à la fois acheteur et vendeur. | POC | |
| EF-10 | Chaque utilisateur dispose d'un espace personnel : achats et ventes en cours, historique, notifications auxquelles il est abonné. | POC partiel | Le POC couvre les notifications et les centres d'intérêt. Achats et ventes : cible |
| EF-11 | Après une transaction, l'acheteur note le vendeur et le vendeur note l'acheteur. | Cible | |

### 2.3 Notifications

| ID | Exigence | Périmètre | Remarque |
| --- | --- | --- | --- |
| EF-12 | Un acheteur authentifié paramètre ses centres d'intérêt depuis son profil. | POC | Centres d'intérêt = catégories dans le POC. Mots-clés : cible |
| EF-13 | Un acheteur est notifié de la mise en ligne d'un nouvel article correspondant à l'un de ses centres d'intérêt. | POC | |
| EF-14 | Un acheteur suit un article précis. Il est notifié quand le prix de cet article change. | POC | |
| EF-15 | Un acheteur règle les types de notifications qu'il reçoit (nouvel article, changement de prix) et les canaux (espace personnel, email). | POC | |
| EF-16 | Les notifications sont listées dans l'espace personnel et peuvent aussi être envoyées par email. | POC partiel | Liste dans l'espace : POC. Envoi d'email : cible (le POC enregistre le canal choisi) |

### 2.4 Paiement

| ID | Exigence | Périmètre | Remarque |
| --- | --- | --- | --- |
| EF-17 | Le paiement se fait exclusivement via la plateforme. Les paiements directs entre particuliers sont proscrits. | Cible | |
| EF-18 | En V1, seul le paiement par carte bancaire est proposé, via un prestataire de services de paiement (PSP). | Cible | |
| EF-19 | Collector prélève une commission de 5 % sur chaque transaction. | Cible | |
| EF-20 | Les fonds sont conservés en séquestre jusqu'à la confirmation de réception par l'acheteur, ce qui permet à Collector de garantir la qualité du vendeur et de ses produits. | Cible | Exigence ajoutée, cohérente avec la garantie annoncée par le contexte |

### 2.5 Chat

| ID | Exigence | Périmètre | Remarque |
| --- | --- | --- | --- |
| EF-21 | Un chat, accessible depuis l'espace personnel, permet à un acheteur et à un vendeur d'échanger à propos d'un article. Les emails et numéros de téléphone y sont bloqués, avec les mêmes règles que pour les articles. | Cible | Réutilise le moteur de contrôle de RM-02 |
| EF-22 | L'administrateur modère le chat : il consulte les conversations signalées et masque ou supprime des messages. | Cible | |

### 2.6 Détection de fraude

| ID | Exigence | Périmètre | Remarque |
| --- | --- | --- | --- |
| EF-23 | Le composant de détection de fraude reçoit les événements de publication d'article et de changement de prix. | POC | Événements `article.published` et `article.price_changed` |
| EF-24 | Le composant détecte les anomalies : prix trop élevé, hausse de prix brutale, vendeur suspect (modifications de prix répétées). | POC | Règles RM-07 |
| EF-25 | La V1 s'intègre à un outil de détection de fraude qui peut être développé en interne ou acheté. | POC partiel | Le POC fournit un service interne. Le contrat d'événements versionné permet de le remplacer par un produit du marché sans modifier le catalogue |
| EF-26 | L'administrateur consulte les alertes de fraude et leur détail. | POC | |

### 2.7 Back-office

| ID | Exigence | Périmètre | Remarque |
| --- | --- | --- | --- |
| EF-27 | Seul l'administrateur crée les catégories du site. | POC | |
| EF-28 | L'administrateur supprime les articles ou suspend les vendeurs qui ne respectent pas la charte de la plateforme. | Cible | |
| EF-29 | L'administrateur traite une file de revue manuelle pour les articles que le contrôle automatique ne peut pas trancher. | Cible | Le POC tranche toujours automatiquement : publié ou rejeté |

### 2.8 Recommandations

| ID | Exigence | Périmètre | Remarque |
| --- | --- | --- | --- |
| EF-30 | Un acheteur authentifié reçoit des recommandations d'articles fondées sur ses centres d'intérêt. | Cible | Les centres d'intérêt saisis dans le POC (EF-12) alimenteront ce service |
| EF-31 | En V2, les recommandations tiennent aussi compte du parcours de l'utilisateur dans le catalogue. | Cible | Collecte d'événements de navigation |

### 2.9 Publicité

| ID | Exigence | Périmètre | Remarque |
| --- | --- | --- | --- |
| EF-32 | La plateforme automatise au maximum la diffusion de publicités ciblées sur des sites partenaires. | Cible | Soumise au consentement RGPD (ENF-10) |

### 2.10 Internationalisation et accessibilité

| ID | Exigence | Périmètre | Remarque |
| --- | --- | --- | --- |
| EF-33 | L'interface est internationalisée : textes traduits (français et anglais au lancement), prix et dates formatés selon la langue de l'utilisateur. | POC | react-i18next, `Intl.NumberFormat` |
| EF-34 | L'interface est accessible (voir ENF-25). | POC partiel | |

### 2.11 Évolutivité fonctionnelle

| ID | Exigence | Périmètre | Remarque |
| --- | --- | --- | --- |
| EF-35 | L'architecture permet d'ajouter rapidement de nouvelles fonctionnalités sans modifier l'existant : enchères, événements de vente en direct (streaming), bot d'avant-vente, analyse des ventes pour la direction. | POC partiel | Le POC le démontre : notification et fraude sont deux consommateurs indépendants des mêmes événements, ajoutés sans toucher au catalogue (voir ADR 0001) |

## 3. Règles métier du POC

Ces règles précisent les exigences implémentées. Les critères d'acceptation et les tests s'appuient dessus.

| ID | Règle |
| --- | --- |
| RM-01 | **Champs d'un article.** Titre de 5 à 120 caractères. Description de 20 à 5 000 caractères. Prix strictement positif, au plus 1 000 000 €, avec 2 décimales au maximum. Frais de port positifs ou nuls. Catégorie existante. Entre 1 et 10 photos (URL `https`). La boutique appartient au vendeur authentifié. |
| RM-02 | **Données personnelles.** Le titre et la description ne contiennent ni adresse email ni numéro de téléphone (formats français et international, y compris avec espaces, points ou tirets). La même règle s'applique au nom et à la description d'une boutique. |
| RM-03 | **Résultat du contrôle.** Le contrôle est synchrone. Un article conforme passe au statut `PUBLISHED` et l'événement `article.published` est émis. Un article non conforme sur le fond (RM-02) est enregistré au statut `REJECTED` avec la liste des motifs, sans événement. Une requête mal formée (champ manquant, type invalide, prix ≤ 0) est refusée avec le code 422 et rien n'est enregistré. |
| RM-04 | **Modification de prix.** Seul le propriétaire de l'article modifie son prix. Seul un article `PUBLISHED` peut changer de prix (sinon 409). Le nouveau prix respecte RM-01. Chaque modification ajoute une ligne à l'historique et émet `article.price_changed`. Un prix identique à l'actuel ne crée ni ligne ni événement. |
| RM-05 | **Boutique.** Nom de 3 à 60 caractères, unique sur la plateforme sans tenir compte de la casse. Chaque boutique porte le type de vendeur `INDIVIDUAL` (particulier), affiché sur la page publique. |
| RM-06 | **Catégorie.** Nom de 2 à 60 caractères, unique sans tenir compte de la casse. Le slug (identifiant d'URL) est dérivé du nom. |
| RM-07 | **Règles anti-fraude.** `PRICE_ABOVE_CEILING` : prix supérieur au plafond configuré (10 000 € par défaut, car le segment de Collector exclut le luxe). `PRICE_SPIKE` : hausse de plus de 50 % en une modification. `FREQUENT_PRICE_CHANGES` : plus de 3 modifications de prix du même article en 24 h. Chaque déclenchement crée une alerte avec sa règle, sa sévérité et l'événement source. |
| RM-08 | **Destinataires des notifications.** `article.published` : les acheteurs qui ont la catégorie de l'article dans leurs centres d'intérêt et le type « nouvel article » activé. `article.price_changed` : les acheteurs qui suivent l'article et ont le type « changement de prix » activé. Le vendeur de l'article n'est jamais notifié de ses propres articles. |
| RM-09 | **Idempotence.** Un consommateur qui reçoit deux fois le même événement (même `event_id`) ne le traite qu'une fois : pas de notification ni d'alerte en double. |

## 4. Exigences non fonctionnelles

Les exigences non fonctionnelles sont classées selon le modèle de qualité produit de l'**ISO/IEC 25010:2023**. L'édition 2023 a renommé deux caractéristiques de l'édition 2011 : *Utilisabilité* devient **Capacité d'interaction** et *Portabilité* devient **Flexibilité**. La scalabilité y est désormais une sous-caractéristique explicite de la flexibilité.

Chaque exigence a une cible mesurable et un moyen de vérification. Les quatre indicateurs qualité du processus (docs/01-qualite) seront choisis parmi ces mesures.

### 4.1 Sécurité

| ID | Exigence | Sous-caractéristique | Cible et vérification | Périmètre |
| --- | --- | --- | --- | --- |
| ENF-01 | Tout flux exposé à l'extérieur du cluster passe en HTTPS (TLS 1.2 minimum). HTTP est redirigé vers HTTPS. | Confidentialité, intégrité | Certificats émis par cert-manager. Vérification : `curl -I http://…` renvoie 308, scan ZAP | POC |
| ENF-02 | L'authentification repose sur OpenID Connect (flux *Authorization Code* avec PKCE). Le jeton d'accès reste en mémoire dans le navigateur. Chaque API valide la signature RS256 du JWT, son émetteur (`iss`), son audience (`aud`) et son expiration (`exp`). | Authenticité | Durée de vie du jeton d'accès : 5 min. Tests : jeton absent, expiré ou falsifié → 401 | POC |
| ENF-03 | L'autorisation est vérifiée côté API : contrôle du rôle (RBAC) puis de la propriété de la ressource (un vendeur ne modifie que ses boutiques et ses articles). | Confidentialité, intégrité | Tests : mauvais rôle → 403, ressource d'un autre vendeur → 403 | POC |
| ENF-04 | Aucun secret n'est versionné. Les secrets sont injectés par des Secrets Kubernetes. | Confidentialité | Gitleaks bloquant en CI | POC |
| ENF-05 | Les vulnérabilités sont détectées automatiquement à chaque modification : analyse statique (Semgrep, Bandit), dépendances (pip-audit, npm audit), images (Trivy), application en fonctionnement (OWASP ZAP baseline). | Résistance | Pipeline bloqué sur toute vulnérabilité CRITICAL ou HIGH qui a un correctif disponible | POC |
| ENF-06 | Les flux réseau internes sont restreints par des NetworkPolicies en refus par défaut. Chaque base de données n'est joignable que par son service. | Confidentialité, résistance | Test : connexion de `fraud-service` vers la base du catalogue refusée | POC |
| ENF-07 | Les entrées sont validées strictement (schémas Pydantic, champs inconnus refusés). L'accès aux données passe par des requêtes paramétrées (ORM), ce qui protège des injections SQL. | Intégrité | Tests de données invalides → 422 | POC |
| ENF-08 | Les actions sont traçables : logs JSON avec identifiant de corrélation et identifiant de l'utilisateur (`sub`), historique des prix horodaté avec son auteur. | Responsabilité, non-répudiation | Revue des logs lors de la démo | POC |
| ENF-09 | Aucune donnée de carte bancaire n'est stockée ni ne transite par Collector : la saisie est déléguée au PSP, qui renvoie un jeton (conformité PCI DSS, niveau SAQ A). | Confidentialité | Audit d'architecture | Cible |
| ENF-10 | Les données personnelles sont traitées conformément au RGPD : minimisation, droit à l'effacement, consentement explicite pour la publicité ciblée. | Confidentialité | Registre des traitements | Cible |
| ENF-11 | Le débit est limité à l'entrée (Ingress et API Gateway) pour résister au déni de service applicatif et au bourrage d'identifiants. | Résistance | Plan de remédiation (docs/06-securite) | Cible |

### 4.2 Efficacité de performance

| ID | Exigence | Sous-caractéristique | Cible et vérification | Périmètre |
| --- | --- | --- | --- | --- |
| ENF-12 | Le temps de réponse reste court sous charge nominale. | Comportement temporel | Avec 50 utilisateurs simultanés (Locust) : p95 < 300 ms en lecture du catalogue, p95 < 500 ms en publication d'article | POC |
| ENF-13 | Le taux d'erreur reste faible sous charge nominale. | Capacité | Moins de 1 % de réponses 5xx sur le scénario Locust | POC |
| ENF-14 | Une notification est disponible peu après l'événement qui la déclenche. | Comportement temporel | p95 < 2 s entre l'horodatage de l'événement et la création de la notification | POC |
| ENF-15 | Les services consomment des ressources bornées. | Utilisation des ressources | Requests et limits CPU et mémoire définis pour chaque pod, consommation suivie dans Grafana | POC |

### 4.3 Fiabilité

| ID | Exigence | Sous-caractéristique | Cible et vérification | Périmètre |
| --- | --- | --- | --- | --- |
| ENF-16 | Les services restent disponibles en cas de panne d'une instance ou d'un nœud. | Disponibilité, tolérance aux pannes | 2 réplicas minimum répartis sur des nœuds différents, PodDisruptionBudget, sondes `liveness` et `readiness`. Démo : arrêt d'un nœud agent sans interruption du service | POC |
| ENF-17 | La plateforme vise une disponibilité mensuelle de 99,5 % en production. | Disponibilité | Supervision par sondes externes et budget d'erreur | Cible |
| ENF-18 | Aucun événement métier n'est perdu. Un événement est émis si et seulement si la modification en base est validée (patron *transactional outbox*). Livraison « au moins une fois » : messages persistants, files durables, acquittement manuel après traitement, file des messages en échec (*dead-letter queue*). | Tolérance aux pannes, absence de défaut | Test d'intégration : broker arrêté pendant une publication, puis événement reçu après son redémarrage | POC |
| ENF-19 | Les consommateurs sont idempotents (RM-09). | Absence de défaut | Test : même événement livré deux fois → une seule notification | POC |
| ENF-20 | Les données sont sauvegardées et restaurables. | Récupérabilité | Sauvegarde PostgreSQL quotidienne, RPO de 24 h, RTO de 4 h | Cible |

### 4.4 Maintenabilité

| ID | Exigence | Sous-caractéristique | Cible et vérification | Périmètre |
| --- | --- | --- | --- | --- |
| ENF-21 | Chaque service possède ses données (une base par service) et ne communique avec les autres que par une API REST versionnée (`/api/v1`) ou par des événements. Aucune base n'est partagée. | Modularité, modifiabilité | Revue d'architecture, NetworkPolicies | POC |
| ENF-22 | Le code métier est couvert par des tests automatisés. | Testabilité | Couverture ≥ 80 % (pytest-cov), quality gate SonarCloud bloquante | POC |
| ENF-23 | La dette technique est maîtrisée. | Analysabilité, modifiabilité | SonarCloud : note de maintenabilité A, duplication < 3 %, complexité cognitive ≤ 15 par fonction. Ruff et mypy (mode strict) bloquants en CI | POC |
| ENF-24 | Le comportement des services est observable. | Analysabilité | Endpoints `/metrics` collectés par Prometheus, tableaux de bord Grafana, logs JSON corrélés, endpoints `/health/live` et `/health/ready` | POC |

### 4.5 Capacité d'interaction

| ID | Exigence | Sous-caractéristique | Cible et vérification | Périmètre |
| --- | --- | --- | --- | --- |
| ENF-25 | L'interface respecte le niveau AA des WCAG 2.1, référentiel repris par le RGAA 4.1 en France. | Inclusivité | Score Lighthouse accessibilité ≥ 90 sur les pages du POC, contrôle axe dans les tests Playwright. Audit RGAA complet : cible | POC partiel |
| ENF-26 | L'interface est utilisable sur mobile. | Capacité d'apprentissage, inclusivité | Mise en page adaptative à partir de 360 px de large | POC |

### 4.6 Compatibilité

| ID | Exigence | Sous-caractéristique | Cible et vérification | Périmètre |
| --- | --- | --- | --- | --- |
| ENF-27 | Les API sont décrites par un contrat OpenAPI 3.1. Les événements ont un schéma JSON versionné (champ `schema_version`). | Interopérabilité | OpenAPI générée par FastAPI, schémas d'événements dans `docs/02-architecture/contrats.md` | POC |
| ENF-28 | L'outil anti-fraude est remplaçable par un produit tiers sans modifier les producteurs d'événements. | Interopérabilité, coexistence | Le contrat d'événements est la seule dépendance | POC |

### 4.7 Flexibilité

| ID | Exigence | Sous-caractéristique | Cible et vérification | Périmètre |
| --- | --- | --- | --- | --- |
| ENF-29 | La charge absorbée augmente par ajout d'instances (scalabilité horizontale). | Scalabilité | HorizontalPodAutoscaler sur `catalog-service` : de 2 à 5 réplicas à 70 % de CPU. Démontré par le test de charge | POC |
| ENF-30 | La plateforme s'installe de façon reproductible. | Installabilité | Cluster, infrastructure et services déployés par script, Helm et Argo CD (GitOps) en moins de 15 min sur un poste vierge | POC |
| ENF-31 | Le déploiement ne dépend pas d'un fournisseur. | Adaptabilité | Charts Helm standards et images multi-architecture (amd64, arm64). La migration vers Oracle OKE ne nécessite aucune modification de code | POC partiel |

## 5. Synthèse

| | POC | POC partiel | Cible | Total |
| --- | --- | --- | --- | --- |
| Exigences fonctionnelles | 14 | 8 | 13 | 35 |
| Exigences non fonctionnelles | 24 | 2 | 5 | 31 |

Le POC concentre l'effort sur la chaîne **publication → contrôle → événements → notification et détection de fraude**, qui exerce à la fois le découpage en services, la communication asynchrone, la sécurité et l'orchestration. Paiement, chat, notation, recommandations, publicité et enchères restent dans l'architecture cible.
