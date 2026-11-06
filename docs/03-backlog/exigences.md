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
| Outil anti-fraude (cible) | Composant interne ou produit acheté, qui s'abonnera aux événements du catalogue. Absent du POC, qui prévoit son point d'extension. | compte de service |

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
| EF-13 | Un acheteur est notifié de la mise en ligne d'un nouvel article correspondant à l'un de ses centres d'intérêt. | POC | L'alerte sur un article particulier relève d'EF-36 (cible) |
| EF-14 | Un acheteur intéressé par un article est notifié quand son prix change. | POC partiel | Dans le POC, l'intérêt pour un article découle de sa catégorie (RM-08). Suivre un article précis : cible |
| EF-15 | Un acheteur règle les types de notifications qu'il reçoit (nouvel article, changement de prix) et les canaux (espace personnel, email). | POC partiel | Types de notification : POC. Choix du canal email : cible |
| EF-16 | Les notifications sont listées dans l'espace personnel et peuvent aussi être envoyées par email. | POC partiel | Liste dans l'espace : POC. Envoi d'email : cible |
| EF-36 | Un acheteur enregistre une recherche précise (mots-clés, catégorie, prix maximal) et est notifié de la mise en ligne d'un article correspondant : c'est le « nouvel article particulier » du contexte. | Cible | Identifiant ajouté après la première version : les identifiants ne sont jamais renumérotés |

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
| EF-23 | Le composant de détection de fraude reçoit les événements de publication d'article et de changement de prix. | Cible | Le POC émet déjà ces événements sur l'exchange `article.events` (EF-25) |
| EF-24 | Le composant détecte les anomalies : prix trop élevé, hausse de prix brutale, vendeur suspect. | Cible | Règles RM-07 |
| EF-25 | La V1 s'intègre à un outil de détection de fraude qui peut être développé en interne ou acheté. | POC partiel | **Point d'extension** : l'outil, interne ou acheté, s'abonnera à l'exchange `article.events` avec sa propre file, sans modification de `catalog-service`. Le POC le démontre en liant une file supplémentaire pendant la démo |
| EF-26 | L'administrateur consulte les alertes de fraude, avec pour chacune la règle déclenchée, les valeurs en cause et l'événement source, et statue dessus. | Cible | |

### 2.7 Back-office

| ID | Exigence | Périmètre | Remarque |
| --- | --- | --- | --- |
| EF-27 | Seul l'administrateur crée les catégories du site. | POC | |
| EF-28 | L'administrateur supprime les articles, et suspend ou supprime les vendeurs, qui ne respectent pas la charte de la plateforme. | Cible | |
| EF-29 | L'administrateur traite une file de revue manuelle pour les articles que le contrôle automatique ne peut pas trancher. Ces articles restent au statut `PENDING_REVIEW`, hors du catalogue, jusqu'à la décision. | Cible | Le POC n'applique que des règles déterministes et tranche donc toujours : publié ou rejeté |

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
| EF-33 | L'interface est internationalisée : textes traduits (français et anglais au lancement), prix et dates formatés selon la langue de l'utilisateur. | Cible | L'interface du POC est en français uniquement (ADR 0007) |
| EF-34 | L'interface est accessible (voir ENF-25). | Cible | Les composants MUI du POC respectent les patrons ARIA, sans contrôle outillé (ADR 0007) |

### 2.11 Évolutivité fonctionnelle

| ID | Exigence | Périmètre | Remarque |
| --- | --- | --- | --- |
| EF-35 | L'architecture permet d'ajouter rapidement de nouvelles fonctionnalités sans modifier l'existant : enchères, événements de vente en direct (streaming), bot d'avant-vente, analyse des ventes pour la direction. | POC partiel | Le POC le démontre : `notification-service` consomme les événements du catalogue sans que celui-ci le connaisse, et une file supplémentaire liée à l'exchange reçoit les mêmes événements sans aucune modification (ADR 0001) |

## 3. Règles métier du POC

Ces règles précisent les exigences implémentées. Les critères d'acceptation et les tests s'appuient dessus.

| ID | Règle |
| --- | --- |
| RM-01 | **Champs d'un article.** Titre de 5 à 120 caractères. Description de 20 à 5 000 caractères. Prix strictement positif, au plus 1 000 000 €, avec 2 décimales au maximum. Frais de port positifs ou nuls. Catégorie existante. Entre 1 et 10 photos (URL `https`). La boutique appartient au vendeur authentifié. |
| RM-02 | **Données personnelles.** Le titre et la description ne contiennent ni adresse email ni numéro de téléphone (formats français et international, y compris avec espaces, points ou tirets). Motifs : `CONTACT_EMAIL`, `CONTACT_PHONE`. La même règle et les mêmes motifs s'appliquent au nom et à la description d'une boutique. **Limite assumée** : les formes obfusquées (« zéro six… », « arobase ») et le texte incrusté dans les photos ne sont pas détectés par le POC. Ils relèvent de la modération de la cible (EF-29). |
| RM-03 | **Résultat du contrôle.** Le contrôle est synchrone. Un article conforme passe au statut `PUBLISHED` et l'événement `article.published` est émis. Un article non conforme sur le fond (RM-02) est enregistré au statut `REJECTED` avec la liste des motifs, sans événement : le rejet est conservé pour la traçabilité, la future revue manuelle (EF-29) et les statistiques de fraude. Une requête mal formée (champ manquant, type invalide, prix ≤ 0) est refusée avec le code 422 et rien n'est enregistré. |
| RM-04 | **Modification de prix.** Seul le propriétaire de l'article modifie son prix. Seul un article `PUBLISHED` peut changer de prix (sinon 409). Le nouveau prix respecte RM-01. Chaque modification ajoute une ligne à l'historique et émet `article.price_changed`. Un prix identique à l'actuel ne crée ni ligne ni événement. |
| RM-05 | **Boutique.** Nom de 3 à 60 caractères, unique sur la plateforme sans tenir compte de la casse. Chaque boutique porte le type de vendeur `INDIVIDUAL` (particulier), affiché sur la page publique. Une boutique qui enfreint RM-02 est **refusée** (422, motifs `CONTACT_EMAIL` ou `CONTACT_PHONE`) et non enregistrée. Contrairement à un article, une boutique n'a pas de cycle de modération : il n'y a ni statut à conserver ni revue à prévoir, donc rien à tracer. |
| RM-06 | **Catégorie.** Nom de 2 à 60 caractères, unique sans tenir compte de la casse. Le slug (identifiant d'URL) est dérivé du nom. |
| RM-07 | **Règles anti-fraude (cible).** `PRICE_ABOVE_CEILING` : prix supérieur au plafond configuré (10 000 € par défaut, car le segment de Collector exclut le luxe). `PRICE_SPIKE` : hausse de plus de 50 % en une modification. `FREQUENT_PRICE_CHANGES` : plus de 3 modifications de prix du même article en 24 h. Chaque déclenchement crée une alerte avec sa règle, sa sévérité et l'événement source. |
| RM-08 | **Destinataires des notifications.** Un acheteur est intéressé par un article si la catégorie de l'article fait partie de ses centres d'intérêt. `article.published` : les acheteurs intéressés qui ont le type « nouvel article » activé. `article.price_changed` : les acheteurs intéressés qui ont le type « changement de prix » activé. Le vendeur de l'article n'est jamais notifié de ses propres articles. |
| RM-09 | **Pas de notification en double.** Un même événement (même `event_id`) ne produit qu'une notification par acheteur, grâce à la contrainte d'unicité `(user_id, source_event_id)` de la table `notifications`. Cette contrainte ne coûte rien et suffit au POC. L'idempotence générale des consommateurs (table `processed_events`) relève de la cible. |

## 4. Exigences non fonctionnelles

Les exigences non fonctionnelles sont classées selon le modèle de qualité produit de l'**ISO/IEC 25010:2023**. L'édition 2023 a renommé deux caractéristiques de l'édition 2011 : *Utilisabilité* devient **Capacité d'interaction** et *Portabilité* devient **Flexibilité**. La scalabilité y est désormais une sous-caractéristique explicite de la flexibilité. L'édition 2023 ajoute aussi la caractéristique **Sûreté** (*Safety* : absence de risque pour les personnes, les biens ou l'environnement). Elle ne s'applique pas à une place de marché en ligne et n'est donc pas déclinée ici.

Chaque exigence a une cible mesurable et un moyen de vérification. Les quatre indicateurs qualité du processus (docs/01-qualite) seront choisis parmi ces mesures.

### 4.1 Sécurité

| ID | Exigence | Sous-caractéristique | Cible et vérification | Périmètre |
| --- | --- | --- | --- | --- |
| ENF-01 | Tout flux exposé à l'extérieur du cluster passe en HTTPS (TLS 1.2 minimum). HTTP est redirigé vers HTTPS. | Confidentialité, intégrité | Certificat générique `*.127.0.0.1.sslip.io` généré une fois par mkcert et chargé dans Traefik comme Secret TLS. Vérification : `curl -I http://…` renvoie une redirection permanente vers HTTPS, scan ZAP | POC |
| ENF-02 | L'authentification repose sur OpenID Connect (flux *Authorization Code* avec PKCE). Le jeton d'accès reste en mémoire dans le navigateur. Chaque API valide la signature RS256 du JWT, son émetteur (`iss`), son audience (`aud`) et son expiration (`exp`). | Authenticité | Durée de vie du jeton d'accès : 5 min. Tests d'acceptation : jeton absent → 401. Tests unitaires : jeton expiré ou falsifié → 401 | POC |
| ENF-03 | L'autorisation est vérifiée côté API : contrôle du rôle (RBAC) puis de la propriété de la ressource (un vendeur ne modifie que ses boutiques et ses articles). | Confidentialité, intégrité | Tests : mauvais rôle → 403, ressource d'un autre vendeur → 403 | POC |
| ENF-04 | Aucun secret n'est versionné. Les secrets sont injectés par des Secrets Kubernetes. | Confidentialité | `.env` ignoré par Git, analyse des secrets de Trivy en CI. Gitleaks sur tout l'historique : cible | POC |
| ENF-05 | Les vulnérabilités sont détectées automatiquement à chaque modification : analyse statique du code (SonarCloud), dépendances et images Docker (Trivy). L'application en fonctionnement est analysée par OWASP ZAP lors de l'audit de sécurité. | Résistance | Pipeline bloqué par Trivy sur toute vulnérabilité CRITICAL ou HIGH qui a un correctif disponible. Semgrep, Bandit, pip-audit et ZAP intégrés à la CI : cible | POC partiel |
| ENF-06 | Les flux réseau internes sont restreints par des NetworkPolicies en refus par défaut. Chaque base de données n'est joignable que par son service. | Confidentialité, résistance | Dans le POC, l'isolation des données passe par les droits PostgreSQL (ENF-21), pas par le réseau. NetworkPolicies : cible | Cible |
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
| ENF-14 | Une notification est disponible peu après l'événement qui la déclenche. | Comportement temporel | p95 < 2 s entre l'horodatage de l'événement et la création de la notification (mesuré par `notification_delay_seconds`) | POC |
| ENF-15 | Les services consomment des ressources bornées. | Utilisation des ressources | Requests et limits CPU et mémoire définis pour chaque pod, consommation suivie dans Grafana | POC |

### 4.3 Fiabilité

| ID | Exigence | Sous-caractéristique | Cible et vérification | Périmètre |
| --- | --- | --- | --- | --- |
| ENF-16 | Les services restent disponibles lors de la perte d'une instance. | Disponibilité, tolérance aux pannes | 2 réplicas par service et sondes `liveness` et `readiness`. Démo : suppression d'un pod pendant un test Locust, recréé automatiquement par son Deployment, taux d'erreur mesuré. Perte d'un nœud entier (répartition imposée, PodDisruptionBudget) : cible | POC partiel |
| ENF-17 | La plateforme vise une disponibilité mensuelle de 99,5 % en production. | Disponibilité | Supervision par sondes externes et budget d'erreur | Cible |
| ENF-18 | Aucun événement métier n'est perdu. Un événement est émis si et seulement si la modification en base est validée (patron *transactional outbox*). Livraison « au moins une fois », file des messages en échec (*dead-letter queue*). | Tolérance aux pannes, absence de défaut | **POC** : publication juste après le commit, message persistant, file durable, acquittement après traitement. Un événement peut être perdu si le broker est indisponible entre le commit et la publication (limite assumée, ADR 0007). Outbox et DLQ : cible | POC partiel |
| ENF-19 | Les consommateurs sont idempotents (RM-09). | Absence de défaut | POC : contrainte d'unicité sur les notifications. Table `processed_events` générale : cible | POC partiel |
| ENF-20 | Les données sont sauvegardées et restaurables. | Récupérabilité | Sauvegarde PostgreSQL quotidienne, RPO de 24 h, RTO de 4 h | Cible |

### 4.4 Maintenabilité

| ID | Exigence | Sous-caractéristique | Cible et vérification | Périmètre |
| --- | --- | --- | --- | --- |
| ENF-21 | Chaque service possède ses données et ne communique avec les autres que par une API REST versionnée (`/api/v1`) ou par des événements. Aucune base n'est partagée. | Modularité, modifiabilité | POC : une instance PostgreSQL, une base logique par service (`catalog_db`, `notification_db`), un utilisateur PostgreSQL par service sans droit de connexion à la base de l'autre. Vérification : connexion refusée. Instance séparée et répliquée par service : cible | POC |
| ENF-22 | Le code métier est couvert par des tests automatisés. | Testabilité | Couverture ≥ 80 % (pytest-cov), quality gate SonarCloud bloquante | POC |
| ENF-23 | La dette technique est maîtrisée. | Analysabilité, modifiabilité | SonarCloud : note de maintenabilité A, duplication < 3 %, complexité cognitive ≤ 15 par fonction. Ruff et mypy (mode strict) bloquants en CI | POC |
| ENF-24 | Le comportement des services est observable. | Analysabilité | Endpoints `/metrics` collectés par Prometheus, tableaux de bord Grafana, logs JSON corrélés, endpoints `/health/live` et `/health/ready` | POC |

### 4.5 Capacité d'interaction

| ID | Exigence | Sous-caractéristique | Cible et vérification | Périmètre |
| --- | --- | --- | --- | --- |
| ENF-25 | L'interface respecte le niveau AA des WCAG 2.1, référentiel repris par le RGAA 4.1 en France. | Inclusivité | Score Lighthouse accessibilité ≥ 90, contrôle axe dans les tests de bout en bout, audit RGAA | Cible |
| ENF-26 | L'interface est utilisable sur mobile. | Opérabilité, inclusivité | Mise en page adaptative à partir de 360 px de large | Cible |

### 4.6 Compatibilité

| ID | Exigence | Sous-caractéristique | Cible et vérification | Périmètre |
| --- | --- | --- | --- | --- |
| ENF-27 | Les API sont décrites par un contrat OpenAPI 3.1. Les événements ont un schéma JSON versionné (champ `schema_version`). | Interopérabilité | OpenAPI générée par FastAPI, schémas d'événements dans `docs/02-architecture/contrats.md` | POC |

### 4.7 Flexibilité

| ID | Exigence | Sous-caractéristique | Cible et vérification | Périmètre |
| --- | --- | --- | --- | --- |
| ENF-29 | La charge absorbée augmente par ajout d'instances (scalabilité horizontale). | Scalabilité | HorizontalPodAutoscaler défini par le chart pour chaque service : de 2 à 5 réplicas à 70 % de CPU. Démontré sur `catalog-service` par le test de charge Locust | POC |
| ENF-30 | La plateforme s'installe de façon reproductible. | Installabilité | Cluster, infrastructure et services déployés par script (`deploy/local/deploy.sh`, `helm upgrade --install`) en moins de 15 min sur un poste vierge. Déploiement GitOps (Argo CD) : cible | POC |
| ENF-31 | Le déploiement ne dépend pas d'un fournisseur. | Adaptabilité | Charts Helm standards et images multi-architecture (amd64, arm64). La migration vers Oracle OKE ne nécessite aucune modification de code | POC partiel |
| ENF-28 | L'outil anti-fraude est remplaçable par un produit tiers sans modifier les producteurs d'événements. | Remplaçabilité | Le contrat d'événements et l'exchange `article.events` sont sa seule dépendance | POC partiel |

## 5. Synthèse

| | POC | POC partiel | Cible | Total |
| --- | --- | --- | --- | --- |
| Exigences fonctionnelles | 8 | 9 | 19 | 36 |
| Exigences non fonctionnelles | 17 | 6 | 8 | 31 |

Le POC concentre l'effort sur la chaîne **publication → contrôle → événement → notification**, qui exerce à la fois le découpage en services, la communication asynchrone, la sécurité et l'orchestration, avec le minimum de composants (ADR 0007). La détection de fraude, le paiement, le chat, la notation, les recommandations, la publicité et les enchères restent dans l'architecture cible.
