# Contenu du support de présentation (20 minutes)

Ce document est la **matière du diaporama** : pour chaque diapositive, le titre, le message, le contenu à afficher, le visuel, les chiffres avec leur source, les critères servis, ce que Lucas dit et la transition. Le diaporama se construit à partir de lui, sans rien ajouter. Les chiffres viennent de fichiers du dépôt, cités à côté ; [`verifier-guide.py`](verifier-guide.py) contrôle que les liens et les visuels existent, que chaque chiffre se retrouve dans sa source et que le minutage totalise 20 minutes.

Sources de cadrage : [guide du jury](guide-jury.md) (preuves et chiffres par critère), [script de la démonstration](demo/script-demo.md), consignes de l'évaluation (`Consignes eval bloc Superviser et Assurer D‚veloppment.pdf`, à la racine du dépôt) et grille d'évaluation.

## Ce que disent les consignes sur la présentation

- **Format** : présentation orale de 20 minutes, suivie de 15 minutes d'échange (consignes, page 1). La mission se « clôture par une présentation à l'entreprise de vos résultats » (page 3).
- **Aucun ordre ni plan imposé.** Les consignes décrivent la mission en 3 phases (structuration du processus, développement et déploiement, plan de remédiation) mais ne fixent pas le plan de l'exposé. Le plan ci-dessous suit un récit (besoin, architecture, preuves, démonstration, qualité, sécurité, équipe) et la correspondance avec les 3 phases est donnée plus bas.
- **Une seule exigence explicite pour l'oral** : « Lors de la présentation vous devrez présenter la montée en charge de l'application en lançant des tests de charge avec Siege ou JMeter par exemple » (page 5). Le POC utilise Locust, du même type : la démonstration lance le test en direct (étape 3).
- Les consignes précisent aussi qu'on n'est pas pénalisé si le pipeline n'a pas d'étape de déploiement en (pré) production, et qu'au moins deux types de tests doivent être intégrés au pipeline ; quatre indicateurs de qualité sont demandés (le POC en mesure cinq).

## Plan minuté

**20 minutes au total : 14 diapositives (14 min) et une démonstration de 6 minutes.** La démonstration est placée après le pipeline : elle montre le pipeline réel, le parcours métier et la montée en charge, puis les diapositives suivantes lisent ce qu'elle vient de prouver. Le script de démonstration mesure 5 min 10 s et garde 50 s de marge : les 6 minutes les contiennent.

| N° | Titre de la diapositive | Durée | Cumul (fin) |
| --- | --- | --- | --- |
| 1 | Collector a besoin d'un contrôle automatique des annonces | 1:00 | 1:00 |
| 2 | Une architecture cible complète, un POC réduit à l'essentiel | 1:00 | 2:00 |
| 3 | Les deux services ne s'appellent jamais directement : ils échangent par événements | 1:00 | 3:00 |
| 4 | La sécurité et l'orchestration sont dans le POC dès le départ | 1:00 | 4:00 |
| 5 | Cinq expérimentations, chacune finit par une décision | 1:00 | 5:00 |
| 6 | Publier, contrôler, notifier : la fonctionnalité répond au besoin | 0:45 | 5:45 |
| 7 | Le pipeline réel est conforme au schéma et bloque sur les défauts | 1:15 | 7:00 |
| D | **Démonstration en direct** (pipeline, parcours métier, pic de charge) | 6:00 | 13:00 |
| 8 | Montée en charge et disponibilité sont démontrées, sur un cluster local | 1:00 | 14:00 |
| 9 | Cinq indicateurs mesurés, aucun hors seuil, la dette est chiffrée | 1:15 | 15:15 |
| 10 | Dix types de tests formalisés, neuf appliqués avec résultats, tous verts | 1:00 | 16:15 |
| 11 | La sécurité est intégrée à chaque étape : dix-sept bonnes pratiques prouvées, des limites assumées | 0:45 | 17:00 |
| 12 | Le plan de remédiation priorise 58 actions sur tout le système d'information | 1:00 | 18:00 |
| 13 | Une formation de 28 heures et trois recrutements envisagés couvrent les écarts critiques | 1:00 | 19:00 |
| 14 | Des limites connues, une suite claire, dix critères couverts | 1:00 | 20:00 |

Vérification : 1:00 × 5 + 0:45 + 1:15 + 6:00 + 1:00 + 1:15 + 1:00 + 0:45 + 1:00 × 3 + 1:00 = 20:00 (le script contrôle la somme de la colonne « Durée »).

**Si le temps manque pendant l'exposé** (dans l'ordre) : abréger la diapositive 11 (deux phrases), puis la 2 (une phrase), puis la 14 (limites en une phrase). Ne jamais rogner la démonstration ni les diapositives 7, 8 et 12.

**Les notes orales font de 100 à 160 mots, soit 45 à 80 s de parole** au rythme d'environ 130 mots par minute (le script de vérification contrôle cette fourchette). Le brief demandait 60 à 90 s, mais 14 diapositives en 14 minutes donnent 60 s en moyenne. Les chiffres sont arrondis à l'oral et exacts dans les tableaux « Chiffres et sources », que le script recoupe avec leurs sources, diapositive par diapositive. **Les chiffres écrits dans les notes orales ne sont pas contrôlés automatiquement** : ils reprennent ceux du tableau de la même diapositive, à relire à la main si une note change.

### Ordre de l'exposé et les 3 phases des consignes

| Phase des consignes | Diapositives |
| --- | --- |
| 1. Structuration du processus (indicateurs, DevSecOps, CI/CD, tests, compétences) | 7, 9, 10, 11, 13 |
| 2. Développement et déploiement (exigences, architecture, expérimentations, POC, observabilité, montée en charge) | 1 à 6, démonstration, 8 |
| 3. Plan de remédiation (analyse de sécurité et recommandations) | 11, 12, 14 |

## Correspondance diapositive et critère

| Critère de la grille | Diapositives qui le servent | Preuve la plus forte à l'écran |
| --- | --- | --- |
| 1. Protocole d'expérimentation | 5 (méthode et décisions), 8, annexe A3 | Tableau des 5 protocoles avec décision et mesure |
| 2. Qualité du POC (découpage, communication, sécurité, hébergement) | 2, 3, 4 | Schéma des deux services reliés par RabbitMQ, 17 critères d'acceptation sur 17 |
| 3. Fonctionnalité métier | 1, 6, démonstration (étape 2) | Captures « publié » et « rejeté », notification de chloe |
| 4. CI/CD | 7, démonstration (étape 1), annexe A1 | `pipeline-cicd.svg` et run de 11 jobs verts |
| 5. Environnement d'exécution | 4, 8, démonstration (étape 3), annexe A3 | Capture Grafana du pic : réplicas de 2 à 5, 0 erreur |
| 6. Indicateurs qualité | 9 | Tableau des 5 indicateurs avec dette et axes |
| 7. Tests | 10 | Pyramide des tests et résultats par type |
| 8. Sécurité | 11, 12, annexes A2 et A4 | Cycle DevSecOps, synthèse du plan de 58 actions |
| 9. Compétences | 13 | Écarts, formation de 28 heures, trois profils |
| 10. Présentation | 14 et l'ensemble (un message par diapositive, démonstration préparée) | Démonstration minutée, schémas lisibles |

## Visuels : existants et à dessiner

| Visuel | État | Diapositive | Remarque de lisibilité |
| --- | --- | --- | --- |
| [`pipeline-cicd.svg`](../01-qualite/img/pipeline-cicd.svg) | Existant, utilisé tel quel | 7 | Rapport 3 : 1, texte lisible en plein écran ; vérifier en projection |
| [`cycle-devsecops.svg`](../01-qualite/img/cycle-devsecops.svg) | Existant, utilisé tel quel | 11 | Rapport 2,6 : 1, lisible |
| [`pyramide-tests.svg`](../01-qualite/img/pyramide-tests.svg) | Existant, utilisé tel quel | 10 | Rapport 1,75 : 1, lisible |
| [`grafana-pic-catalog-service.png`](../04-experimentations/05-charge-disponibilite/resultats/20261106-1132/grafana-pic-catalog-service.png) | Existant, **à remplacer par la nouvelle capture (axe du panneau « Taux d'erreur » corrigé)**, même chemin | 8 | Lisible ; l'axe actuel va jusqu'à « 10000 % » alors que le taux est à 0 |
| [Captures 01, 03, 04 et 06](../../frontend/e2e/resultats/captures/) | Existantes, utilisées telles quelles | 1, 6 | Lisibles ; à placer côte à côte |
| [`pipeline-backend.svg`](../01-qualite/img/pipeline-backend.svg), [`matrice-risques.svg`](../06-securite/img/matrice-risques.svg), [`sequence-authentification.svg`](../02-architecture/img/sequence-authentification.svg) | Existants, en annexe seulement | A1, A2, A6 | Denses : réservés aux questions |
| [`architecture-poc.svg`](../02-architecture/img/architecture-poc.svg) | **Existant mais à ne pas projeter** : en annexe A5 | (diapositive 3) | 3 638 × 793, rapport 4,6 : 1 : le texte devient minuscule sur un écran 16:9. Remplacé par un schéma simplifié |
| [`architecture-cible.svg`](../02-architecture/img/architecture-cible.svg) | **Existant mais à ne pas projeter** | (diapositive 2) | 2 067 × 2 315 (portrait) : illisible en diapositive. Remplacé par un tableau à 4 lignes |
| Tableau « cible et POC » | **À dessiner** | 2 | 4 lignes, 3 colonnes |
| Schéma simplifié des deux services | **À dessiner par le chef dans le diaporama** | 3 | 6 boîtes, 5 flèches |
| Tableau « verrous de sécurité et orchestration » | **À dessiner** | 4 | 4 lignes |
| Tableau des 5 protocoles | **À dessiner** | 5 | 4 lignes |
| Trois chiffres de la disponibilité | **À dessiner** (à côté de la capture Grafana) | 8 | 3 grands nombres |
| Tableau des 5 indicateurs | **À dessiner** | 9 | 4 lignes, 4 colonnes |
| Schéma du plan en 3 horizons | **À dessiner** | 12 | 3 colonnes de hauteurs proportionnelles |
| Tableau des écarts de compétences | **À dessiner** | 13 | 4 lignes |
| Carte de démonstration | **À dessiner** | D | 3 lignes (étapes de la démonstration), fond neutre |

## Les diapositives

### Diapositive 1 — Collector a besoin d'un contrôle automatique des annonces

**Minutes** : 1:00, cumul 1:00.

**Message clé** : Collector vend entre particuliers et prend 5 % de commission, donc il faut empêcher les ventes hors plateforme dès la publication, et le POC prouve cette chaîne.

**Contenu** (4 puces) :

- Collector.shop : vente d'objets de collection entre particuliers, commission de 5 % sur chaque transaction.
- Besoin : un article n'est mis en vente qu'après contrôle, automatisé le plus possible, sans email ni téléphone dans le texte.
- Besoin : les acheteurs intéressés sont prévenus d'un nouvel article ou d'un changement de prix.
- Mission du Lead Developer : un POC avec pipeline CI/CD, déploiement orchestré, sécurité minimale, puis un plan de remédiation.

**Visuel** : capture [`01-catalogue-public.png`](../../frontend/e2e/resultats/captures/01-catalogue-public.png) (le catalogue public), occupant la moitié droite.

**Chiffres et sources** :

| Chiffre | Source |
| --- | --- |
| Commission de 5 % | [exigences, EF-19](../03-backlog/exigences.md) |
| 5 user stories, 17 points, 17 critères d'acceptation | [user stories](../03-backlog/user-stories.md) |

**Critères** : 3 (besoin), 10 (message unique).

**Notes orales** : « Bonjour. Collector est une start-up qui lance une application de vente d'objets de collection entre particuliers : baskets en édition limitée, figurines, cassettes. Elle gagne 5 % sur chaque vente. Cela crée un risque : si un vendeur donne son numéro de téléphone, l'acheteur et lui peuvent conclure hors du site, et Collector perd sa commission. Le besoin métier est donc double. Un article ne doit être mis en vente qu'après un contrôle, le plus automatique possible. Et les acheteurs intéressés doivent être prévenus. Ma mission de Lead Developer, c'est de montrer, avec un prototype, qu'on peut livrer cette chaîne de façon fiable, sécurisée et mesurée. J'ai donc réalisé cinq user stories, avec dix-sept critères d'acceptation. Je vous montre d'abord comment le système est conçu. »

**Transition** : « Pour tenir ce besoin, j'ai conçu une architecture cible, puis un POC volontairement plus petit. »

### Diapositive 2 — Une architecture cible complète, un POC réduit à l'essentiel

**Minutes** : 1:00, cumul 2:00.

**Message clé** : le POC n'implémente que la tranche qui démontre chaque point évalué, et chaque élément retiré est un risque connu, suivi dans le plan de remédiation.

**Contenu** (tableau de 4 lignes) :

| Sujet | Architecture cible | POC |
| --- | --- | --- |
| Anti-fraude | Service `fraud-service` | Point d'extension : il s'abonnera à l'exchange `article.events` |
| Fiabilité des événements | Outbox, files de reprise | Publication juste après le commit (limite L2) |
| Données | PostgreSQL par service, répliqué | Une instance, une base et un utilisateur par service (L3) |
| Déploiement | Argo CD, opérateurs, cert-manager | Script `deploy.sh`, images officielles, certificat mkcert |

**Visuel** : tableau à dessiner (4 lignes, 3 colonnes). Ne pas projeter [`architecture-cible.svg`](../02-architecture/img/architecture-cible.svg) (portrait, illisible).

**Chiffres et sources** :

| Chiffre | Source |
| --- | --- |
| Limites assumées L1 à L25 | [architecture du POC, section 8](../02-architecture/architecture-poc.md#8-limites-assumées-du-poc) |

**Critères** : 2 (cohérence cible et POC).

**Notes orales** : « J'ai dessiné deux architectures. La cible est complète : un service anti-fraude, une file de reprise pour ne perdre aucun événement, des bases séparées, un déploiement continu avec Argo CD. Le POC, lui, retient la solution la plus simple qui démontre chaque point évalué. Ce n'est pas un oubli : chaque élément retiré est écrit comme une limite, de L1 à L25, avec son risque et sa recommandation. Par exemple, la publication des événements se fait juste après l'enregistrement en base, sans outbox : si le broker est arrêté à cet instant, l'événement est perdu. Je le sais, je l'ai écrit, et c'est dans le plan de remédiation. Le service anti-fraude demandé par le contexte n'est pas développé, mais il se branchera sur le flux d'événements sans modifier le catalogue. »

**Transition** : « Voyons ce découpage en deux services. »

### Diapositive 3 — Les deux services ne s'appellent jamais directement : ils échangent par événements

**Minutes** : 1:00, cumul 3:00.

**Message clé** : le catalogue et les notifications sont deux services indépendants reliés par RabbitMQ, ce qui permet d'ajouter un service sans toucher aux autres.

**Contenu** (schéma) : navigateur, Ingress Traefik (HTTPS), `catalog-service`, RabbitMQ (exchange `article.events`), `notification-service`, Keycloak, PostgreSQL (une base par service).

**Visuel** : **schéma simplifié à dessiner par le chef dans le diaporama**, de gauche à droite : Navigateur → Traefik → `catalog-service` → RabbitMQ (`article.events`) → `notification-service`. Keycloak en haut, relié aux deux services par « clés de signature » (trait distinct des événements) ; PostgreSQL en bas avec deux cylindres, `catalog_db` et `notification_db`, chacun relié à son service. Une boîte pointillée « futur service anti-fraude » branchée sur RabbitMQ. La vue complète [`architecture-poc.svg`](../02-architecture/img/architecture-poc.svg) (rapport 4,6 : 1, illisible en diapositive) va en annexe A5.

**Chiffres et sources** :

| Chiffre | Source |
| --- | --- |
| Livraison « au moins une fois » : 1 message relivré sur 1 000, 0 doublon traité | [index des expérimentations](../04-experimentations/README.md) |
| Aucun appel HTTP entre services | [CLAUDE.md, décisions d'architecture](../../CLAUDE.md) |

**Critères** : 2 (découpage, communication interservice).

**Notes orales** : « Voici le découpage. Le service catalogue gère les catégories, les boutiques, les articles et le contrôle automatique. Le service notification gère les centres d'intérêt et les notifications. Ces deux services ne s'appellent jamais directement : ils échangent par événements. Quand un article est publié, le catalogue envoie un événement dans RabbitMQ, un courtier de messages, et le service notification le reçoit et prévient les acheteurs concernés. L'événement contient déjà ce qu'il faut : catégorie, vendeur, titre, prix. Le futur service anti-fraude n'aura qu'à s'abonner au même flux. Chaque service a sa base et son utilisateur PostgreSQL. Seule exception, Keycloak : chaque service lui demande les clés publiques qui servent à vérifier les jetons. Enfin, RabbitMQ livre au moins une fois : une contrainte d'unicité en base évite les doublons, et j'ai mesuré zéro doublon traité. »

**Transition** : « Cette architecture est sécurisée et orchestrée dès le POC. »

### Diapositive 4 — La sécurité et l'orchestration sont dans le POC dès le départ

**Minutes** : 1:00, cumul 4:00.

**Message clé** : le POC valide la sécurité (HTTPS en entrée, identité, autorisation) et l'orchestration (Kubernetes, Helm, autoscaling) sur un vrai cluster à trois nœuds, et dit ce qui n'est pas chiffré.

**Contenu** (tableau de 4 lignes) :

| Verrou | Ce qui est en place |
| --- | --- |
| HTTPS | Tout ce qui entre dans le cluster passe en HTTPS (Ingress Traefik, certificat mkcert) ; le trafic interne (JWKS, SQL, AMQP) n'est pas chiffré (L10) |
| Identité | Keycloak, OIDC avec PKCE, jeton d'accès de 5 minutes gardé en mémoire |
| Autorisation | Chaque service vérifie lui-même le jeton JWT (signature RS256, émetteur, audience, expiration), puis le rôle et la propriété |
| Orchestration | Cluster k3d (1 server + 2 agents), chart Helm, 2 réplicas minimum, sondes, HPA de 2 à 5 |

**Visuel** : tableau à dessiner (4 lignes, 2 colonnes). Option : [`placement-noeuds.svg`](../02-architecture/img/placement-noeuds.svg) en réserve pour la question « et si un nœud tombe ».

**Chiffres et sources** :

| Chiffre | Source |
| --- | --- |
| Jeton d'accès de 5 minutes, PKCE | [architecture du POC, section 5](../02-architecture/architecture-poc.md#5-points-de-sécurité) |
| 15 cas d'autorisation conformes | [index des expérimentations](../04-experimentations/README.md) |
| Cluster 1 server + 2 agents, HPA de 2 à 5 réplicas à 70 % de CPU | [architecture du POC, section 4](../02-architecture/architecture-poc.md#4-disponibilité-et-montée-en-charge) |
| Trafic interne non chiffré : limite L10 (chiffrement du trafic interne, mTLS) | [architecture du POC, section 8](../02-architecture/architecture-poc.md#8-limites-assumées-du-poc) |

**Critères** : 2 (sécurité, hébergement et orchestration), 5 (environnement managé), 8 (bonnes pratiques).

**Notes orales** : « Côté sécurité, trois choses. Un : tout ce qui entre dans le cluster passe en HTTPS, terminé par l'Ingress Traefik, la porte d'entrée. Attention, le trafic interne, entre les pods, n'est pas chiffré : c'est la limite L10, dans le plan. Deux : l'identité est gérée par Keycloak avec le protocole OIDC et sa variante PKCE, qui protège le code d'autorisation. Le jeton reste en mémoire du navigateur et dure cinq minutes. Trois : chaque service vérifie lui-même le jeton JWT, sans faire confiance au réseau interne. Côté orchestration, j'utilise un vrai cluster Kubernetes, k3d, avec un nœud de contrôle et deux nœuds de travail. Un chart Helm, c'est un paquet de manifestes Kubernetes paramétrés : il décrit deux copies minimum de chaque service, des sondes de santé et un autoscaler horizontal, le HPA, qui monte jusqu'à cinq copies quand le processeur dépasse 70 %. »

**Transition** : « Avant de développer, j'ai testé chaque technologie critique. »

### Diapositive 5 — Cinq expérimentations, chacune finit par une décision

**Minutes** : 1:00, cumul 5:00.

**Message clé** : chaque technologie critique a été testée sur un cluster jetable, avec un protocole rejouable par script : interactions, mesures, difficultés, limites et décision.

**Contenu** (tableau de 4 lignes, plus une puce) :

| Expérimentation | Interactions testées | Mesure et décision | Difficulté résolue |
| --- | --- | --- | --- |
| 1. RabbitMQ | Producteur, exchange, file, consommateur | 0 message perdu sur 2 × 1 000 ; 10 s au lieu de 54 s avec l'opérateur : adopté, opérateur abandonné | Redémarrage en boucle dû à `fsGroup` (cookie Erlang) |
| 2. Keycloak, Traefik, TLS | Navigateur, Traefik, Keycloak, API, clés JWKS | 15 cas d'autorisation conformes : adopté | Sondes en HTTPS sur un port en HTTP |
| 3. Observabilité | API, Prometheus, Grafana | Environ 600 Mi : adopté, version allégée | Opérateur bloqué faute de Secret de certificat |
| 4 et 5. Déploiement, charge | GHCR, Helm, cluster ; Locust, HPA | 199 s depuis rien ; 2 à 5 réplicas prêts en 60 s : adoptés | Grafana tué par manque de mémoire |

- Kafka, écarté sans essai : surdimensionné pour la V1, empreinte mémoire JVM (ADR 0003).

**Visuel** : tableau à dessiner (4 lignes, 4 colonnes) et une ligne de bas de page pour Kafka.

**Chiffres et sources** :

| Chiffre | Source |
| --- | --- |
| 0 message perdu sur 2 × 1 000 ; 10 s au lieu de 54 s | [index des expérimentations](../04-experimentations/README.md) |
| 15 cas d'autorisation conformes ; environ 600 Mi | [index des expérimentations](../04-experimentations/README.md) |
| 199 s depuis rien ; 2 à 5 réplicas prêts en 60 s | [index des expérimentations](../04-experimentations/README.md) |
| Difficultés : `fsGroup` du broker, sondes de Keycloak, Secret de l'opérateur, mémoire de Grafana | [protocole 1](../04-experimentations/01-rabbitmq/protocole.md), [2](../04-experimentations/02-keycloak-tls/protocole.md), [3](../04-experimentations/03-observabilite/protocole.md) et [5](../04-experimentations/05-charge-disponibilite/protocole.md), section 6 |
| Kafka : surdimensionné pour la V1, empreinte mémoire JVM | [ADR 0003](../02-architecture/adr/0003-rabbitmq-plutot-que-kafka.md) |

**Critères** : 1 (protocole, interactions, difficultés, décisions), 5 (mesures sur l'environnement).

**Notes orales** : « Un protocole d'expérimentation n'est pas un guide d'installation. Chacun des miens suit huit rubriques : la question posée, les technologies et leurs interactions, l'environnement avec les versions exactes, les étapes rejouables par un script, les résultats mesurés, les difficultés, les limites et la décision. Premier exemple, RabbitMQ : producteur, exchange, file, consommateur. J'ai supprimé le pod du broker en envoyant des messages, aucun message perdu, et sans opérateur le broker revient en dix secondes au lieu de cinquante-quatre : j'ai abandonné l'opérateur. Une difficulté : un réglage de droits sur le volume empêchait le redémarrage, je l'ai retiré. Keycloak : quinze cas d'autorisation vérifiés. Observabilité : environ six cents mégaoctets, version allégée. Les deux derniers protocoles mesurent le déploiement et la montée en charge. Kafka est écarté sans essai : trop lourd pour ce besoin. »

**Transition** : « Voyons maintenant la fonctionnalité métier réalisée sur cette base. »

### Diapositive 6 — Publier, contrôler, notifier : la fonctionnalité répond au besoin

**Minutes** : 0:45, cumul 5:45.

**Message clé** : cinq user stories couvrent la chaîne ; un article conforme est publié, un article avec un téléphone est rejeté avec son motif, l'acheteur intéressé est notifié, et les 17 critères d'acceptation passent.

**Contenu** (4 puces) :

- US-01 et US-02 : l'admin crée une catégorie, le vendeur crée sa boutique.
- US-03 Publication : champs, prix positif, aucun email ni téléphone, sinon `REJECTED` avec le motif.
- US-04 Prix : historique conservé, deuxième événement.
- US-05 Notification : l'acheteur qui suit la catégorie la reçoit, sans doublon.

**Visuel** : trois captures côte à côte, [article publié](../../frontend/e2e/resultats/captures/03-vendre-article-publie.png), [article rejeté](../../frontend/e2e/resultats/captures/04-vendre-article-rejete.png) et [notifications de chloe](../../frontend/e2e/resultats/captures/06-notifications-chloe.png).

**Chiffres et sources** :

| Chiffre | Source |
| --- | --- |
| 17 critères d'acceptation sur 17, en 9,84 s | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) |
| 6 parcours Playwright sur 6 | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) |

**Critères** : 3 (fonctionnalité métier), 7 (tests d'acceptation).

**Notes orales** : « La fonctionnalité réalisée suit le besoin, en cinq user stories. Les deux premières préparent le terrain : l'administrateur crée les catégories, le vendeur crée sa boutique. Troisième : une vendeuse publie un article, et le service vérifie les champs, que le prix est positif et qu'il n'y a ni adresse email ni numéro de téléphone. Si tout va bien, l'article est publié. Sinon il est rejeté et la réponse donne le motif : les deux premières captures montrent les deux cas. Quatrième : quand le prix change, l'historique est conservé et un second événement part. Cinquième : les acheteurs qui suivent la catégorie reçoivent leurs notifications, comme sur la troisième capture. Chaque critère d'acceptation est un test automatique, et dix-sept sur dix-sept passent. Dans quelques minutes, vous le verrez en direct. »

**Transition** : « Cette fonctionnalité est livrée par un pipeline que je vais vous montrer. »

### Diapositive 7 — Le pipeline réel est conforme au schéma et bloque sur les défauts

**Minutes** : 1:15, cumul 7:00.

**Message clé** : le pipeline GitHub Actions suit le schéma, la preuve est écrite ligne par ligne, il bloque la livraison sur un défaut de qualité ou de sécurité et chaque image est traçable jusqu'au commit.

**Contenu** (schéma) : le schéma de livraison de la CI au déploiement par script, avec ses conditions : jobs de `lint` à `acceptance` à chaque push, `sonar` sur `main` et les pull requests, `publish` sur `main` seulement.

**Visuel** : [`pipeline-cicd.svg`](../01-qualite/img/pipeline-cicd.svg), pleine largeur. Le détail des jobs est dit une seule fois, dans l'étape 1b de la démonstration, et dessiné en annexe A1 ([`pipeline-backend.svg`](../01-qualite/img/pipeline-backend.svg)).

**Chiffres et sources** :

| Chiffre | Source |
| --- | --- |
| Run `backend` de référence : 11 jobs verts, run 42219458020 | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) |
| Premier run de référence : durée totale 5 min 47 s, 9 jobs verts | [conformité du pipeline](../01-qualite/conformite-pipeline.md) |
| Run 43064777792 : 8 min 37 s | [script de la démonstration](demo/script-demo.md) |
| 6 jobs par service | [schéma CI/CD](../01-qualite/cicd.md) |

**Critères** : 4 (processus schématisé et pipeline réel), 7 (tests dans le pipeline), 6 (outils qui alimentent les indicateurs), 8 (SAST et SCA bloquants).

**Notes orales** : « Voici le processus de livraison, schématisé, et le pipeline réel qui lui correspond. Pour chaque élément du schéma, un document de conformité donne la ligne du fichier de workflow et un run qui le prouve. Les règles : à chaque push, les contrôles de style, les tests, le scan de l'image et les tests d'acceptation ; l'analyse SonarCloud sur la branche principale et les pull requests, à cause du plan gratuit ; la publication des images uniquement sur la branche principale. Les outils couvrent deux familles : SAST, l'analyse statique du code, avec SonarCloud ; SCA, l'analyse des dépendances et de l'image, avec Trivy. Un défaut bloque tout, et trois blocages sont prouvés par des runs rouges : le lint, le quality gate de Sonar et le scan Trivy. Chaque image porte le tag "sha" du commit et un digest : on remonte du pod au commit. Le détail des étapes, je vous le montre en direct. »

**Transition** : « Place à la démonstration : le pipeline, le parcours métier et le pic de charge. »

### Démonstration en direct (6 minutes)

**Minutes** : 6:00, de 7:00 à 13:00.

**Message clé** : tout ce qui vient d'être décrit fonctionne en direct sur le cluster, de la livraison à la montée en charge.

**Contenu** (3 étapes, détail dans le [script de la démonstration](demo/script-demo.md)) :

| Étape | Durée | Ce que le jury voit |
| --- | --- | --- |
| 1. Pipeline et déploiement | 1 min 20 | Run vert du commit du jour, déploiement du même tag, smoke test, digest |
| 2. Parcours métier | 1 min 55 | Alice publie, un article est rejeté, le prix baisse, chloe est notifiée |
| 3. Pic de charge, Grafana, pod supprimé | 1 min 55 | L'HPA de 2 à 5 pods, p95 sous le seuil, remplacement du pod sans erreur |

**Visuel** : carte de démonstration à dessiner (3 lignes), affichée en attente pendant les changements de fenêtre ; sinon, plein écran sur les applications.

**Chiffres et sources** :

| Chiffre | Source |
| --- | --- |
| Étapes de 1 min 20, 1 min 55 et 1 min 55 ; total 5 min 10 avec 50 s de marge | [script de la démonstration](demo/script-demo.md) |

**Critères** : 10 (démonstration préparée), 3, 4 et 5.

**Notes orales** : à dire au lancement : « Je lance le déploiement du commit que la CI vient de publier, et pendant qu'il tourne je vous montre le pipeline. » Le reste du discours est dans le script de démonstration, étape par étape. Plan de secours : captures de [`frontend/e2e/resultats/captures/`](../../frontend/e2e/resultats/captures/), capture Grafana de la diapositive 8, puis la vidéo de secours.

**Transition** : « Revenons aux diapositives : lisons ce que cette démonstration vient de prouver. »

### Diapositive 8 — Montée en charge et disponibilité sont démontrées, sur un cluster local

**Minutes** : 1:00, cumul 14:00.

**Message clé** : sous un pic de 200 utilisateurs (protocole 5) l'HPA passe de 2 à 5 pods en une minute sans erreur, et un pod supprimé en pleine charge est remplacé en 5 secondes sans requête perdue ; l'environnement est un cluster Kubernetes local.

**Contenu** (3 grands nombres à côté de la capture) :

- 2 à 5 réplicas prêts en 60 s.
- Pod supprimé remplacé en 4,9 s, 0 échec sur 533 requêtes.
- 0 réponse 5xx sur 20 235 requêtes.

**Visuel** : [`grafana-pic-catalog-service.png`](../04-experimentations/05-charge-disponibilite/resultats/20261106-1132/grafana-pic-catalog-service.png) (débit, latence p95, taux d'erreur, réplicas), les trois chiffres à droite en grand. **À remplacer par la nouvelle capture (axe du panneau « Taux d'erreur » corrigé)** quand le chef l'aura refaite ; le chemin reste le même.

**Chiffres et sources** :

| Chiffre | Source |
| --- | --- |
| 2 à 5 réplicas prêts en 60 s (200 utilisateurs) | [index des expérimentations](../04-experimentations/README.md) |
| Pod remplacé en 4,9 s, 0 échec sur 533 requêtes | [index des expérimentations](../04-experimentations/README.md) |
| Retour à 2 pods en 325 s | [index des expérimentations](../04-experimentations/README.md) |
| 0 réponse 5xx sur 20 235 requêtes | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) |
| Auto-réparation sans charge : 7,1 s | [protocole 4](../04-experimentations/04-deploiement/protocole.md) |
| En direct : 300 utilisateurs simulés | [script de la démonstration](demo/script-demo.md) |
| ADR acceptée sous réserve de la validation de l'intervenant, repli Oracle OKE Always Free | [ADR 0006](../02-architecture/adr/0006-kubernetes-local-k3d-argocd.md) |

**Critères** : 5 (disponibilité et montée en charge démontrées, honnêteté sur le cluster local), 1 (protocole 5).

**Notes orales** : « Ce que vous avez vu en direct est mesuré dans le protocole cinq. Le protocole mesure deux cents utilisateurs ; en direct, j'en lance trois cents, pour être sûr d'atteindre cinq réplicas à froid. Sous le pic du protocole, le HPA a fait passer le catalogue de deux à cinq pods en soixante secondes. Un pod supprimé en pleine charge a été remplacé en moins de cinq secondes, sans requête perdue sur les cinq cent trente-trois envoyées. Sur tout le pic, vingt mille requêtes, zéro erreur serveur. Soyons honnêtes sur l'environnement : c'est un cluster Kubernetes local, pas un service géré. Je l'ai choisi pour son coût nul et sa reproductibilité. Si un environnement managé est exigé, le repli prévu est Oracle OKE, mais je ne l'ai pas testé. Je ne démontre pas de panne de nœud : sans règle de placement, le résultat serait aléatoire. C'est une limite écrite. »

**Transition** : « Ces mesures s'inscrivent dans cinq indicateurs de qualité suivis à chaque version. »

### Diapositive 9 — Cinq indicateurs mesurés, aucun hors seuil, la dette est chiffrée

**Minutes** : 1:15, cumul 15:15.

**Message clé** : cinq indicateurs rattachés à l'ISO 25010 sont mesurés sur le même code des services, tous dans le seuil, et la dette qu'ils révèlent est chiffrée avec une action pour chaque point.

**Contenu** (tableau de 4 lignes) :

| Indicateur | Mesure | Seuil | Dette et axe |
| --- | --- | --- | --- |
| I1 couverture | 98,45 % et 97,66 % | ≥ 80 % | Règle de frais de port à 1 000 000 € absente de RM-01 : à arbitrer |
| I2 dette | 0 min ; duplication 0,0 % | Note A ; < 3 % | 531 lignes recopiées (34,6 %) : paquet partagé |
| I3 charge | p95 de 21 ms et de 23 ms ; 0 sur 6 564 | < 300 ms ; < 500 ms | Plafond de l'HPA vers 200 utilisateurs |
| I4 et I5 | 0 CRITICAL ou HIGH avec correctif ; 17 sur 17 | 0 ; 17 | Bundle front de 609,4 Ko ; 15 erreurs mypy dans les tests |

**Visuel** : tableau à dessiner (4 lignes, 4 colonnes) avec une pastille verte « dans le seuil » par ligne. Note de bas de page : « Mesures sur le même code des services : images de `22364bc`, charge sur `9d2c96e`, code identique. »

**Chiffres et sources** :

| Chiffre | Source |
| --- | --- |
| Couverture de 98,45 % (`catalog-service`) et de 97,66 % (`notification-service`) | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) |
| Dette de 0 min, duplication de 0,0 % (SonarCloud) | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) |
| p95 de 21 ms en lecture, de 23 ms en publication ; 0 sur 6 564 requêtes | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) |
| 0 vulnérabilité CRITICAL ou HIGH avec correctif ; 17 sur 17 | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) |
| Images de `22364bc`, charge sur `9d2c96e`, code des services identique | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) |
| 531 lignes dupliquées (34,6 %) ; 15 erreurs mypy ; bundle de 609,4 Ko | [indicateurs, axes d'amélioration](../01-qualite/indicateurs.md#axes-damélioration-contre-la-dette-technique) |
| Frais de port plafonnés à 1 000 000 €, règle absente de RM-01, à arbitrer | [indicateurs, axes d'amélioration](../01-qualite/indicateurs.md#axes-damélioration-contre-la-dette-technique) |

**Critères** : 6 (indicateurs mesurés et axes d'amélioration), 7 (tests qui alimentent I1 et I5).

**Notes orales** : « Le contexte demande de maîtriser la qualité dans le temps. J'ai retenu cinq indicateurs rattachés à la norme ISO 25010, chacun avec un seuil et un outil. Ils sont mesurés sur le même code des services : images du commit 22364bc, charge mesurée sur 9d2c96e, code identique. La couverture des tests dépasse quatre-vingt-dix-sept pour cent, pour un seuil à quatre-vingts. SonarCloud mesure zéro minute de dette. Sous cinquante utilisateurs, le p95, le temps de réponse de quatre-vingt-quinze pour cent des requêtes, est de vingt et une millisecondes en lecture, pour un seuil de trois cents. Mais mesurer, c'est aussi trouver de la dette que les seuils ne voient pas : cinq cent trente et une lignes recopiées entre les deux services, un plafond de frais de port absent des règles métier, à arbitrer, quinze erreurs de typage dans les tests, un bundle front de six cents kilooctets. Chacune a son action dans le relevé. »

**Transition** : « Ces indicateurs reposent sur un processus de test formalisé. »

### Diapositive 10 — Dix types de tests formalisés, neuf appliqués avec résultats, tous verts

**Minutes** : 1:00, cumul 16:15.

**Message clé** : le processus de test est formalisé (dix types, avec outil, moment, responsable et sortie attendue) et neuf types sont appliqués au POC avec leurs résultats, tous verts ; le dixième, la non-régression, est le rejeu de toute la suite.

**Contenu** (4 repères placés sur la pyramide) :

- Unitaires, intégration et API (pytest, testcontainers) : 289 et 203 tests passés.
- Acceptation (pytest, httpx) : 17 sur 17 ; non-régression : la suite est rejouée à chaque push.
- Front : 62 tests Vitest, 6 parcours Playwright.
- Charge et disponibilité (Locust) ; sécurité : SAST (SonarCloud), SCA (Trivy, `npm audit`), audit dynamique (ZAP).

**Visuel** : [`pyramide-tests.svg`](../01-qualite/img/pyramide-tests.svg), avec les quatre repères en légende à droite.

**Chiffres et sources** :

| Chiffre | Source |
| --- | --- |
| Dix types de tests formalisés (lignes du tableau des types) | [processus de test](../01-qualite/processus-test.md) |
| 289 passed (`catalog-service`) et 203 passed (`notification-service`) | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) |
| 17 passed (acceptation) | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) |
| 62 tests passés (Vitest), 6 parcours sur 6 (Playwright) | [indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) |
| Tous les seuils sont respectés (charge) ; 0 échec sur 533 requêtes (disponibilité) | [résumé de la charge](../../tests/load/resultats/20261106-1106/resume.md) et [index des expérimentations](../04-experimentations/README.md) |
| `catalog-service` relancé le 11/11/2026 sur le dépôt actuel : 294 passed | [fiche P10-01, journal](../suivi/taches/P10-01.md) |

**Critères** : 7 (processus formalisé, deux types ou plus appliqués), 6 (tests qui alimentent I1, I3 et I5).

**Notes orales** : « Le processus de test est écrit : dix types, et pour chacun l'outil, l'endroit dans le dépôt, le moment d'exécution, le responsable et le critère de succès. Neuf sont appliqués avec des résultats ; le dixième, la non-régression, consiste à rejouer toute la suite à chaque push. La pyramide va de nombreux tests rapides en bas à peu de tests lents en haut. En bas, les tests unitaires, d'intégration et d'API avec pytest : deux cent quatre-vingt-neuf pour le catalogue, deux cent trois pour les notifications, avec de vrais PostgreSQL et RabbitMQ jetables. Au milieu, les dix-sept tests d'acceptation, un par critère, dans le pipeline. Côté front, soixante-deux tests de composants et six parcours dans un vrai navigateur. Enfin la charge et la disponibilité avec Locust, et la sécurité : SAST avec Sonar, SCA avec Trivy, audit dynamique avec ZAP. Playwright et Locust tournent à la demande sur le cluster, hors CI. Tout passe. »

**Transition** : « Parlons maintenant de sécurité, à chaque étape du cycle de développement. »

### Diapositive 11 — La sécurité est intégrée à chaque étape : dix-sept bonnes pratiques prouvées, des limites assumées

**Minutes** : 0:45, cumul 17:00.

**Message clé** : la démarche DevSecOps place un contrôle de sécurité à chaque étape, le POC applique dix-sept bonnes pratiques avec une preuve rejouable, et les écarts restants sont nommés.

**Contenu** (4 puces) :

- Identité : authentification OIDC avec PKCE, JWT validé par chaque service ; la MFA est au plan (PA-02, PA-40).
- Conteneurs : les services tournent sans droits root ; RabbitMQ et Keycloak restent à traiter (L17, L18).
- Secrets : aucun secret versionné (`.env` ignoré) ; la recherche de secrets dans l'historique n'est pas en CI (L13).
- Chaîne : SAST (SonarCloud) et SCA (Trivy) bloquants avant publication ; audit ZAP et Trivy rejoué après corrections.

**Visuel** : [`cycle-devsecops.svg`](../01-qualite/img/cycle-devsecops.svg) (huit étapes, de Plan à Monitor), les quatre puces à droite.

**Chiffres et sources** :

| Chiffre | Source |
| --- | --- |
| Dix-sept bonnes pratiques prouvées dans le POC | [plan de remédiation, section 7](../06-securite/plan-remediation.md#7-déjà-appliqué-dans-le-poc) |
| 11 lignes de rapport par service avec correctif avant les corrections, 0 après | [rapport des scans, section 10](../06-securite/rapport-scans.md#10-après-corrections-p9-02) |
| ZAP actif complet : 0 constat de niveau moyen ou élevé | [plan de remédiation, section 7](../06-securite/plan-remediation.md#7-déjà-appliqué-dans-le-poc) |
| MFA au plan : PA-02 et PA-40 | [plan de remédiation](../06-securite/plan-remediation.md) |
| Limites L13 (secrets dans l'historique), L17 et L18 (conteneurs de l'infrastructure) | [architecture du POC, section 8](../02-architecture/architecture-poc.md#8-limites-assumées-du-poc) |

**Critères** : 8 (au moins deux bonnes pratiques dans le POC), 4 (sécurité dans le pipeline), 2 (sécurité du POC).

**Notes orales** : « DevSecOps, c'est mettre la sécurité à chaque étape du cycle plutôt que la contrôler à la fin. Dans le POC, dix-sept bonnes pratiques sont appliquées, chacune avec une preuve : un fichier, un test ou un run. Identité : OIDC avec PKCE, et chaque service valide le jeton JWT ; l'authentification à plusieurs facteurs, elle, est au plan. Conteneurs : les services tournent sans droits root, mais RabbitMQ et Keycloak restent à traiter. Secrets : aucun secret dans Git, mais la recherche de secrets dans l'historique n'est pas encore dans la CI. Chaîne : l'analyse statique SonarCloud et l'analyse Trivy bloquent la publication. J'ai aussi fait un audit avec OWASP ZAP et Trivy : onze lignes de rapport avec correctif par service avant mes corrections, zéro après. Rien n'est parfait, et c'est le sujet de la diapositive suivante. »

**Transition** : « L'audit alimente un plan de remédiation sur tout le système d'information. »

### Diapositive 12 — Le plan de remédiation priorise 58 actions sur tout le système d'information

**Minutes** : 1:00, cumul 18:00.

**Message clé** : 62 risques ont été notés sur le POC, la plateforme cible et le système existant, et 58 actions datées les réduisent en commençant par les 7 critiques.

**Contenu** (schéma en 3 colonnes) :

| Horizon | Actions | Charge |
| --- | --- | --- |
| Court terme (0 à 3 mois) | 29 | 64 j |
| Moyen terme (3 à 6 mois) | 21 | 97,5 j |
| Long terme (6 à 12 mois et plus) | 8 | 64 j |

Deux résultats attendus à 12 mois, en grands nombres : criticité cumulée de 650 à 298, risques critiques de 7 à 0.

**Visuel** : schéma à dessiner, trois colonnes de hauteurs proportionnelles aux actions (29, 21, 8), avec les deux résultats à droite. La [matrice complète des 62 risques](../06-securite/img/matrice-risques.svg) est en annexe A2.

**Chiffres et sources** :

| Chiffre | Source |
| --- | --- |
| Registre de 62 risques : 7 critiques, 30 élevés | [plan de remédiation](../06-securite/plan-remediation.md) |
| 58 actions, 225,5 j | [plan de remédiation, lecture rapide](../06-securite/plan-remediation.md#1-lecture-rapide) |
| Court terme (0 à 3 mois) : 29 actions, 64 j ; moyen terme (3 à 6 mois) : 21 actions, 97,5 j ; long terme (6 à 12 mois et plus) : 8 actions, 64 j | [plan de remédiation, lecture rapide](../06-securite/plan-remediation.md#1-lecture-rapide) |
| Criticité cumulée de 650 aujourd'hui à 298 ; risques critiques de 7 à 0 | [plan de remédiation, lecture rapide](../06-securite/plan-remediation.md#1-lecture-rapide) |

**Critères** : 8 (plan priorisé sur le parc applicatif du SI).

**Notes orales** : « La consigne demande un plan de remédiation priorisé pour tout le système d'information, pas seulement le POC. J'ai donc noté soixante-deux risques sur trois périmètres : le POC, la plateforme cible et le système existant de la start-up, dont l'état est inconnu et traité par des hypothèses. Chaque risque est noté par impact fois probabilité : sept sont critiques, trente élevés. Le plan compte cinquante-huit actions. La règle de priorité est simple : chaque risque critique reçoit au moins une action à court terme, quel que soit l'effort, et les actions peu coûteuses passent en premier. Résultat attendu à douze mois : la criticité cumulée passe de six cent cinquante à deux cent quatre-vingt-dix-huit, et il ne reste plus aucun risque critique. La plateforme n'ouvre aux utilisateurs réels qu'à cette condition. »

**Transition** : « Pour réaliser ce plan, il faut une équipe avec les bonnes compétences. »

### Diapositive 13 — Une formation de 28 heures et trois recrutements envisagés couvrent les écarts critiques

**Minutes** : 1:00, cumul 19:00.

**Message clé** : les compétences sont cartographiées, les écarts critiques sont identifiés, chacun reçoit une réponse adaptée (formation, recrutement envisagé ou appui externe) et une formation est détaillée.

**Contenu** (tableau de 4 lignes) :

| Écart | Réponse |
| --- | --- |
| Kubernetes et Helm (requis 3, maximum de l'équipe 1) | **Formation de 28 heures**, six modules, sur 6 semaines |
| Exploitation de production, sécurité de la chaîne | Recrutement envisagé : DevOps / SRE |
| Tests de charge et de bout en bout | Recrutement envisagé : QA automaticien·ne |
| Accessibilité RGAA ; conformité (RGPD, PCI DSS) et test d'intrusion | Recrutement envisagé : UX/UI avec accessibilité ; appui externe (DPO, prestataire d'intrusion) |

**Visuel** : tableau à dessiner (4 lignes, 2 colonnes) ; la matrice complète des compétences ([matrice.md](../05-competences/matrice.md)) reste en réserve.

**Chiffres et sources** :

| Chiffre | Source |
| --- | --- |
| 26 compétences cartographiées | [matrice de compétences](../05-competences/matrice.md) |
| Trois recrutements envisagés (trois profils) | [matrice de compétences](../05-competences/matrice.md) |
| Formation de 28 heures, six modules, sur 6 semaines | [plan de formation](../05-competences/plan-formation.md) |

**Critères** : 9 (matrice, expertises à acquérir, action de formation).

**Notes orales** : « J'ai cartographié vingt-six compétences, avec le niveau de chaque membre de l'équipe : le Lead Developer et deux développeurs. Les écarts les plus critiques sont Kubernetes et Helm, l'exploitation de production, la sécurité, l'accessibilité et les tests de charge. Je n'ai pas inventé un profil qui sait tout : trois recrutements envisagés, un DevOps, un QA automaticien et un designer UX avec accessibilité, plus de l'appui externe pour le test d'intrusion et la conformité. Les profils des deux développeurs sont des hypothèses, signalées comme telles. L'action de formation porte sur Kubernetes et Helm, parce que le Lead Developer doit pouvoir défendre et exploiter le cluster, même une fois le DevOps arrivé : vingt-huit heures, six modules, six semaines, avec des exercices sur le dépôt réel et une évaluation. »

**Transition** : « Il reste à dire honnêtement ce que le POC ne fait pas encore. »

### Diapositive 14 — Des limites connues, une suite claire, dix critères couverts

**Minutes** : 1:00, cumul 20:00.

**Message clé** : le POC prouve la faisabilité de la chaîne complète, ses limites sont connues et suivies, et la suite est prête à être décidée.

**Contenu** (4 puces) :

- Limites : cluster local, une seule instance PostgreSQL, publication sans outbox, déploiement lancé à la main (L1 à L25).
- Suite : si un Kubernetes managé est exigé, Oracle OKE (le même chart devrait s'y déployer ; non testé à ce jour) ; service anti-fraude sur `article.events`.
- Plan : 58 actions, d'abord les 7 risques critiques.
- Tout se rejoue par script : README suivi sur un cluster neuf.

**Visuel** : schéma à dessiner, trois flèches de gauche à droite, « POC (aujourd'hui) » vers « V1 : Kubernetes managé, outbox, anti-fraude » vers « Plateforme ouverte (aucun risque critique) ».

**Chiffres et sources** :

| Chiffre | Source |
| --- | --- |
| Limites assumées L1 à L25 | [architecture du POC, section 8](../02-architecture/architecture-poc.md#8-limites-assumées-du-poc) |
| README suivi tel quel sur un cluster neuf : 174 s | [fiche P10-01, journal](../suivi/taches/P10-01.md) |
| Déploiement à froid : 199 s depuis rien | [index des expérimentations](../04-experimentations/README.md) |
| 58 actions | [plan de remédiation](../06-securite/plan-remediation.md) |

**Critères** : 10 (discours structuré, conclusion), et rappel de 1 à 9.

**Notes orales** : « Pour conclure. Le POC prouve que la chaîne complète fonctionne : un besoin métier, deux services qui communiquent par événements, un pipeline qui bloque sur les défauts, un cluster qui monte en charge et se répare, des indicateurs mesurés et un plan de sécurité. Ses limites sont connues : un cluster local, une seule instance de base de données, des événements publiés sans outbox, un déploiement lancé à la main. Elles sont numérotées de L1 à L25 et alimentent le plan de remédiation. La suite : si vous exigez un environnement managé, le même chart devrait se déployer sur Oracle OKE, mais je ne l'ai pas encore testé ; puis l'outbox et le service anti-fraude. Tout ce que je vous ai montré se rejoue par script, depuis un cluster vide : le README, suivi tel quel, a donné un déploiement en moins de trois minutes. Merci, je suis prêt pour vos questions. »

**Transition** : fin de l'exposé ; les 15 minutes d'échange suivent (questions et glossaire : tâche P10-04).

## Annexes (diapositives de réserve, hors minutage)

Ces diapositives ne sont pas présentées. Elles servent à répondre aux questions probables du jury.

### Annexe A1 — Détail du pipeline backend

**Question visée** : « Que fait chaque job, et que se passe-t-il quand il échoue ? »

**Visuel** : [`pipeline-backend.svg`](../01-qualite/img/pipeline-backend.svg) (dense : zoomer sur un job à la fois).

**Source** : [schéma CI/CD](../01-qualite/cicd.md) (sections 2 et 3) et [conformité du pipeline](../01-qualite/conformite-pipeline.md) (tableau de conformité et preuves de blocage, runs rouges pour `lint`, `build-scan` et le quality gate).

**À dire** : `sonar` ne tourne que sur `main` et les pull requests (limite du plan gratuit de SonarCloud) ; les actions sont épinglées par empreinte ; Trivy 0.76.0 est un binaire vérifié par somme SHA-256 (choix après la compromission de l'action officielle).

### Annexe A2 — Matrice impact × probabilité des 62 risques

**Question visée** : « Comment avez-vous noté et priorisé les risques ? »

**Visuel** : [`matrice-risques.svg`](../06-securite/img/matrice-risques.svg) (trait plein : position actuelle ; pointillé : position visée pour les 7 critiques).

**Source** : [plan de remédiation, méthode de priorisation](../06-securite/plan-remediation.md#2-méthode-de-priorisation) et [analyse de risques, échelles](../06-securite/analyse-risques.md).

**À dire** : criticité = impact (1 à 5) × probabilité (1 à 5) ; seuils critique ≥ 15, élevé 10 à 14, moyen 5 à 9, faible ≤ 4 ; règle R1 : chaque risque critique a au moins une action à court terme.

### Annexe A3 — Protocole 5 : chronologie de la montée en charge

**Question visée** : « Comment avez-vous mesuré, et sur quelle durée ? »

**Visuel** : [chronologie du protocole 5](../04-experimentations/05-charge-disponibilite/resultats/20261106-1132/resume.md) (tableau d'événements) et, pour le retour à 2 pods, la capture [`grafana-retour-catalog-service.png`](../04-experimentations/05-charge-disponibilite/resultats/20261106-1132/grafana-retour-catalog-service.png).

**Source** : [protocole 5](../04-experimentations/05-charge-disponibilite/protocole.md) (8 rubriques : environnement, étapes, mesures, difficultés, limites, décision).

**À dire** : une seule exécution de référence par scénario, sur le même Mac que le cluster ; l'HPA ne descend qu'après sa fenêtre de stabilisation (protection contre les yoyos), ce qui explique le retour à 2 pods en 325 s.

### Annexe A4 — Flux et STRIDE du POC

**Question visée** : « Quelles menaces avez-vous analysées ? »

**Source** : [analyse de risques, sections 3 (flux et STRIDE) et 4 (OWASP Top 10 et API Security Top 10)](../06-securite/analyse-risques.md) et [rapport des scans](../06-securite/rapport-scans.md) (constats F-01 à F-26 et état après corrections).

**À dire** : STRIDE classe les menaces en six familles (usurpation, altération, répudiation, divulgation, déni de service, élévation de privilèges) ; chaque flux du schéma a ses menaces et ses mesures (S1 à S9).

### Annexe A5 — Vue complète du POC et limites L1 à L25

**Question visée** : « Montrez-moi l'architecture complète. Qu'est-ce qui n'est pas fait, et pourquoi ? »

**Visuel** : [`architecture-poc.svg`](../02-architecture/img/architecture-poc.svg) (vue complète : à zoomer par zone, trop large pour une diapositive).

**Source** : [architecture du POC, section 8](../02-architecture/architecture-poc.md#8-limites-assumées-du-poc) et [ADR 0007](../02-architecture/adr/0007-simplification-perimetre-poc.md).

**À dire** : L1 service anti-fraude, L2 outbox, L3 une seule instance PostgreSQL, L4 NetworkPolicies, L8 placement des réplicas (pas de démonstration de panne de nœud), L10 trafic interne non chiffré, L12 déploiement GitOps ; chacune est rattachée à une action du plan.

### Annexe A6 — Flux d'authentification OIDC avec PKCE

**Question visée** : « Comment le service vérifie-t-il le jeton, et pourquoi deux URL de Keycloak ? »

**Visuel** : [`sequence-authentification.svg`](../02-architecture/img/sequence-authentification.svg).

**Source** : [architecture du POC, section 7](../02-architecture/architecture-poc.md#7-authentification--flux-oidc-avec-pkce) et [ADR 0004](../02-architecture/adr/0004-keycloak.md).

**À dire** : le navigateur obtient son jeton par l'URL publique de Keycloak, le champ `iss` du jeton porte cette URL ; dans un pod, `127.0.0.1` désigne le pod lui-même, donc le service télécharge les clés de signature par l'URL interne du Service Kubernetes, tout en vérifiant que `iss` est l'URL publique.
