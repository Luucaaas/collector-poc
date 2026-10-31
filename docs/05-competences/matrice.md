# Matrice de compétences et recrutements

Ce document répond à la consigne 1.1.3 : cartographier les compétences nécessaires à Collector.shop, évaluer celles de l'équipe IT, puis en déduire les formations et les recrutements. Il reste réaliste : chaque profil recruté couvre un métier précis, aucun ne cumule tout (pas de « mouton à 5 pattes »).

Le périmètre est l'équipe IT du contexte Collector : un·e Lead Developer et deux développeur·euse·s confirmé·e·s de 5 ans d'expérience. Les autres salariés (direction, RH, marketing) n'interviennent que comme parties prenantes.

## 1. Échelle de niveaux

Les niveaux vont de 0 à 4. Chaque niveau se vérifie par des faits observables.

| Niveau | Nom | Critères observables |
| --- | --- | --- |
| 0 | Aucune notion | Ne connaît pas l'outil ou le sujet. Ne sait pas dire à quoi il sert |
| 1 | Notions | Connaît le vocabulaire et le rôle de l'outil. Suit un tutoriel ou un exemple fourni. Ne livre rien seul·e dans cette compétence |
| 2 | Autonome sur les tâches courantes | Réalise seul·e une tâche courante déjà vue (ajouter un endpoint, un test, un job). Lit la documentation officielle. Demande de l'aide sur les cas inhabituels et le diagnostic d'une panne |
| 3 | Maîtrise et peut former | Conçoit une solution complète, diagnostique une panne, arbitre entre plusieurs options. Relit le travail d'autrui et forme les autres |
| 4 | Expert de référence | A conduit cette compétence en production sur plusieurs projets. Fixe les standards de l'équipe, traite les cas rares (performance, incident, montée de version) |

**Règle de lecture.** Le niveau requis est celui dont le projet a besoin pour que l'équipe livre et exploite le produit sans dépendre d'une personne extérieure. Un niveau 3 est requis presque partout : un système en production demande de pouvoir diagnostiquer et former. Le niveau 4 n'est visé que pour un métier recruté.

## 2. Hypothèses sur l'équipe

Le contexte ne décrit pas les profils des développeurs. Les parcours de « Dev 1 » et « Dev 2 » sont des **hypothèses** de ce document, choisies crédibles et complémentaires. Le profil du Lead Developer est réel.

| Membre | Parcours (hypothèse sauf mention) | Forces | Points faibles |
| --- | --- | --- | --- |
| Lead Dev (Lucas) | Réel. Solide en Python. Débutant en React/TypeScript, Kubernetes, Helm et GitHub Actions. Pilote le projet et la qualité | Python, tests, conception d'API | Front, orchestration, CI/CD |
| Dev 1 | 5 ans de développement back-end Python (API REST, PostgreSQL) dans une ESN. A conteneurisé ses services avec Docker et déployé sur des serveurs virtuels. N'a jamais exploité de cluster Kubernetes | Python, SQL, Docker | Front, Kubernetes, accessibilité |
| Dev 2 | 5 ans de développement front-end JavaScript/TypeScript (React) dans une agence web, avec un peu de Node.js. A suivi des maquettes et des intégrations de design système. Peu d'expérience du back-end Python et de l'exploitation | React, TypeScript, tests front | Python, bases de données, conteneurs |

Conséquence : le front-end repose sur une seule personne (Dev 2) et le back-end sur deux (Lead Dev, Dev 1). Le risque de dépendance à Dev 2 est signalé dans l'analyse des écarts.

## 3. Matrice

- **Requis** : niveau nécessaire au projet, de la V1 à la cible (`architecture-cible.md`).
- **Max équipe** : meilleur niveau parmi Lead Dev, Dev 1 et Dev 2.
- **Écart** : requis moins max équipe, au minimum 0.
- **Criticité** : haute si l'écart bloque la livraison ou une exigence explicite du contexte ; moyenne s'il ralentit ou fait courir un risque maîtrisable ; basse sinon. « — » si l'écart est nul.

| Domaine | Compétence | Requis | Lead Dev | Dev 1 | Dev 2 | Max équipe | Écart | Criticité |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Back-end | Python 3.12, FastAPI, Pydantic v2, uv | 3 | 3 | 3 | 1 | 3 | 0 | — |
| Back-end | SQLAlchemy 2.0, Alembic | 3 | 2 | 3 | 1 | 3 | 0 | — |
| Front | React, TypeScript, Vite | 3 | 1 | 1 | 3 | 3 | 0 | — |
| Front | MUI, React Router, react-oidc-context | 2 | 1 | 0 | 3 | 3 | 0 | — |
| Données | PostgreSQL : modèle, index, droits par utilisateur | 3 | 2 | 3 | 2 | 3 | 0 | — |
| Données | PostgreSQL : exploitation (sauvegardes, réplication) | 3 | 1 | 2 | 1 | 2 | 1 | Moyenne |
| Messagerie | RabbitMQ, aio-pika, architecture événementielle (outbox, DLQ) | 3 | 2 | 2 | 1 | 2 | 1 | Moyenne |
| Messagerie | Temps réel : WebSocket (chat acheteur-vendeur) | 3 | 1 | 2 | 2 | 2 | 1 | Moyenne |
| Identité | OIDC, OAuth 2.0, JWT (PKCE, JWKS, audiences), PyJWT | 3 | 2 | 2 | 2 | 2 | 1 | Moyenne |
| Identité | Keycloak : realm, rôles, fédération Entra ID | 3 | 1 | 1 | 0 | 1 | 2 | Moyenne |
| Conteneurs | Docker : images multi-stage, non-root, multi-architecture | 3 | 2 | 3 | 2 | 3 | 0 | — |
| Orchestration | Kubernetes : k3d, déploiement, sondes, HPA, ingress Traefik, TLS (mkcert) | 3 | 1 | 1 | 0 | 1 | 2 | Haute |
| Orchestration | Helm : chart, values, secrets | 3 | 1 | 0 | 0 | 1 | 2 | Haute |
| CI/CD | GitHub Actions, GHCR, GitOps (Argo CD en cible) | 3 | 1 | 2 | 2 | 2 | 1 | Moyenne |
| Observabilité | Prometheus, Grafana (kube-prometheus-stack), logs JSON corrélés (structlog), alertes | 3 | 1 | 1 | 0 | 1 | 2 | Moyenne |
| Tests | pytest, pytest-cov, testcontainers, tests d'acceptation httpx | 3 | 3 | 3 | 2 | 3 | 0 | — |
| Tests | Test de charge (Locust) et analyse des résultats | 3 | 2 | 2 | 1 | 2 | 1 | Moyenne |
| Tests | Vitest, Playwright (tests front et de bout en bout) | 3 | 1 | 1 | 2 | 2 | 1 | Moyenne |
| Sécurité | Sécurité applicative, DevSecOps, OWASP (Ruff, mypy, SonarCloud, Trivy, ZAP) | 3 | 2 | 2 | 2 | 2 | 1 | Haute |
| Paiement | Intégration de paiement : API du PSP, webhooks, 3-D Secure | 2 | 1 | 1 | 1 | 1 | 1 | Moyenne |
| Conformité | RGPD : base légale, consentement, durées, droits des personnes | 3 | 1 | 1 | 1 | 1 | 2 | Moyenne |
| Conformité | PCI DSS par délégation au PSP (périmètre SAQ A) | 2 | 1 | 1 | 1 | 1 | 1 | Moyenne |
| Conformité | Accessibilité RGAA 4.1 / WCAG 2.1 niveau AA | 3 | 1 | 0 | 1 | 1 | 2 | Haute |
| Conformité | Internationalisation (i18n) | 2 | 0 | 1 | 2 | 2 | 0 | — |
| UX/UI | Conception d'interface, parcours, design system | 3 | 1 | 0 | 2 | 2 | 1 | Moyenne |
| Produit | Gestion de produit, agilité (backlog, user stories, revues) | 3 | 2 | 1 | 2 | 2 | 1 | Basse |

Justification de quelques niveaux.

- **Lead Dev : Python et tests à 3, la plupart des autres compétences à 1 ou 2.** Il maîtrise Python. En React/TypeScript, Kubernetes, Helm et GitHub Actions, il n'a que des notions : niveau 1 à chaque fois. Il n'est pas à 4 en Python faute de référence sur plusieurs projets en production. Dans la réalité du POC, il écrit le front en suivant des exemples et avec l'aide d'outils : cela correspond au niveau 1, et l'équipe fictive s'appuie sur Dev 2.
- **Sécurité applicative en criticité haute.** Le contexte la dit « de premier plan » (transactions financières) : un écart de 1 suffit à le classer haute.
- **Dev 2, React à 3 et non 4.** Cinq ans de front en agence donnent la maîtrise, pas la référence sur l'architecture d'une SPA complexe.
- **Aucune cellule à 4 dans l'équipe actuelle.** Cinq ans d'expérience ne font pas d'expert : le niveau 4 s'obtient par un recrutement spécialisé.
- **PCI DSS à 2 requis.** Collector délègue la saisie de la carte au PSP et ne voit qu'un jeton. Il faut comprendre le périmètre et ses obligations, pas auditer un environnement de cartes. La criticité de l'écart reste moyenne et non haute : la saisie de la carte est déléguée au PSP (périmètre SAQ A), Collector ne stocke aucune donnée de carte.
- **Produit et agilité à 3.** Le rôle de Product Owner est tenu par un·e des deux dirigeant·e·s (anciens chefs de projet IT), ce qui limite la criticité de l'écart.

## 4. Analyse des écarts

Les cinq écarts les plus critiques, par ordre de priorité.

| N° | Écart | Risque pour le projet | Réponse retenue |
| --- | --- | --- | --- |
| 1 | Sécurité applicative et DevSecOps (requis 3, max 2, criticité haute) | Le contexte place la sécurité au premier plan : l'application porte des transactions financières. Une faille exploitable (injection, contrôle d'accès défaillant, dépendance vulnérable) expose les comptes et les paiements. Les outils du POC (SonarCloud, Trivy) détectent, mais ne remplacent pas l'œil d'un spécialiste | **Recrutement** du DevOps/SRE, qui sécurise la chaîne de livraison (niveau 3), et **accompagnement externe** : un test d'intrusion annuel par un prestataire indépendant |
| 2 | Kubernetes et Helm (requis 3, max 1, criticité haute), avec l'exploitation de production qui en dépend : observabilité (requis 3, max 1, moyenne) et exploitation de PostgreSQL (requis 3, max 2, moyenne) | La mise en production, la montée en charge et la reprise après incident dépendent d'un outil que personne ne maîtrise. Sans observabilité, une panne passe inaperçue ; sans sauvegarde testée, une perte de données est irréversible. Le POC repose sur un chart et un cluster : sans compétence, le Lead Dev ne peut ni les défendre ni les faire évoluer | **Formation** de l'équipe, en priorité du Lead Dev (niveau 3), puis **recrutement** d'un DevOps/SRE pour l'exploitation de production (niveau 4) |
| 3 | Accessibilité RGAA 4.1 / WCAG 2.1 niveau AA (requis 3, max 1, criticité haute) | L'accessibilité est une exigence explicite du contexte. Sans référent, l'interface est livrée non conforme et la correction après coup coûte plus cher que de concevoir accessible | **Recrutement** d'un·e UX/UI designer avec compétence accessibilité. Le niveau 3 se vérifie sur plusieurs projets, il ne s'acquiert pas en quelques semaines |
| 4 | Conformité et paiement : RGPD (requis 3, max 1), PCI DSS (requis 2, max 1), intégration du PSP (requis 2, max 1), tous de criticité moyenne | Traitement de données personnelles d'acheteurs et de vendeurs sans base légale établie, sanction de la CNIL, atteinte à la confiance. Une erreur de périmètre PCI DSS ou d'intégration du PSP engage la responsabilité de Collector | **Accompagnement externe ponctuel** : un·e DPO ou un cabinet de conformité pour le registre et l'analyse d'impact, un audit du périmètre PCI DSS avant l'ouverture, le support d'intégration du PSP |
| 5 | Tests de charge et de bout en bout (Locust, Playwright ; requis 3, max 2, criticité moyenne) | Les tests de charge et les parcours front sont écrits par des développeurs qui ne sont pas spécialistes : couverture incomplète, tests fragiles, validation de l'acceptation faite par ceux qui codent | **Recrutement** d'un·e QA automaticien·ne, qui reprend la revue des tests et la validation de l'acceptation |

**Écarts non retenus parmi les cinq.** Keycloak n'y figure pas : le realm est importé depuis un JSON versionné et le DevOps apporte le niveau 2, l'écart restant est moyen. Le chat en temps réel (WebSocket) et les parcours UX/UI sont des écarts moyens qui se traitent par la pratique en binôme et la revue de code, sans action dédiée. Les emails transactionnels passent par un fournisseur dédié (`architecture-cible.md`, section 5) : c'est une intégration d'API courante, sans ligne propre dans la matrice. L'outil anti-fraude, développé en interne ou acheté, s'abonne à l'exchange `article.events` : son intégration relève des compétences RabbitMQ et architecture événementielle déjà présentes dans la matrice, et ne crée pas d'écart nouveau.

Choix entre formation, recrutement et accompagnement externe.

| Critère | Formation | Recrutement | Accompagnement externe |
| --- | --- | --- | --- |
| Durée d'acquisition | De l'ordre de quelques semaines pour passer de 1 à 2, de plusieurs mois de pratique pour atteindre 3, de plusieurs années pour atteindre 4 | Niveau 4 disponible dès l'arrivée, après un recrutement de l'ordre de 2 à 4 mois | Immédiate |
| Besoin | Permanent et au cœur du métier de l'équipe | Permanent, mais demandant un métier à plein temps | Ponctuel (audit, analyse d'impact) |
| Retenu pour | Kubernetes et Helm, au niveau 3 : le Lead Dev doit pouvoir superviser, relire un chart et diagnostiquer, sans dépendre d'une seule personne | DevOps, QA, UX/UI : des métiers distincts, à temps plein | Test d'intrusion, RGPD, PCI DSS, support du PSP : peu de jours par an |

**Écart ciblé par l'action de formation.** L'action de formation détaillée (à venir, `plan-formation.md`) vise **Kubernetes et Helm**. C'est l'écart de criticité haute que l'équipe doit maîtriser en interne en permanence : le Lead Dev supervise le déploiement et doit défendre le cluster, même une fois le DevOps arrivé. La sécurité applicative, écart n° 1, est aussi de criticité haute, mais sa réponse est un recrutement et un test d'intrusion externe : on achète ce niveau d'expertise, on ne le forme pas en interne. L'accessibilité, également haute, demande un métier de conception et non une formation de quelques semaines. Kubernetes et Helm restent donc l'écart de criticité haute dont la compétence doit rester dans l'équipe.

## 5. Recrutements envisagés

Trois profils, qui s'articulent avec le RACI de `docs/01-qualite/processus-test.md` : le QA reprend la revue des tests et la validation de l'acceptation, le DevOps reprend l'exécution de la CI et du déploiement. Aucun Product Owner n'est recruté : le rôle est tenu par un·e dirigeant·e.

### 5.1 Ingénieur DevOps / SRE

| Rubrique | Contenu |
| --- | --- |
| Missions | Exploiter le Kubernetes managé de production. Faire évoluer les charts Helm et la CI/CD (GitHub Actions, puis Argo CD). Mettre en place l'observabilité et les alertes. Gérer les sauvegardes et la réplication PostgreSQL. Animer les astreintes |
| Compétences clés | 1. Kubernetes (niveau 4) ; 2. Helm et GitOps (4) ; 3. Observabilité Prometheus/Grafana (3) ; 4. GitHub Actions et sécurité de la chaîne de livraison (3) ; 5. Exploitation PostgreSQL et RabbitMQ en cluster (3) |
| Expérience | 5 ans ou plus en exploitation ou en plateforme, dont 3 ans sur Kubernetes en production, sur plusieurs projets |
| Arrivée | Après le POC, avant la migration vers le Kubernetes managé européen et la première mise en production |
| Écarts couverts | N° 2 (Kubernetes, Helm, observabilité, exploitation PostgreSQL), et en partie n° 1 (sécurité de la chaîne de livraison, complétée par le test d'intrusion externe). Couvre aussi GitHub Actions et RabbitMQ en exploitation |

### 5.2 QA automaticien·ne

| Rubrique | Contenu |
| --- | --- |
| Missions | Définir la stratégie de test avec le Lead Dev. Écrire et maintenir les tests d'acceptation, de bout en bout (Playwright) et de charge (Locust). Revoir les tests des développeurs. Valider l'acceptation avec le Product Owner. Suivre les indicateurs qualité |
| Compétences clés | 1. Playwright et tests de bout en bout (niveau 3) ; 2. Locust et analyse de performance (3) ; 3. pytest et tests d'API (3) ; 4. Conception de cas de test et gestion des anomalies (3) ; 5. Intégration des tests en CI (2) |
| Expérience | 3 à 5 ans en automatisation de tests |
| Arrivée | Dès le premier sprint après le POC, avant la montée en charge de l'équipe de développement |
| Écarts couverts | N° 5 (charge, bout en bout). Ne couvre ni Kubernetes ni l'accessibilité |

### 5.3 UX/UI designer avec compétence accessibilité

| Rubrique | Contenu |
| --- | --- |
| Missions | Concevoir les parcours acheteur, vendeur et back-office, et le design system. Porter l'accessibilité RGAA/WCAG dès la conception. Auditer les écrans livrés. Définir les règles d'internationalisation de l'interface |
| Compétences clés | 1. Conception d'interface et parcours (niveau 3) ; 2. Design system (3) ; 3. RGAA 4.1 / WCAG 2.1 niveau AA (3) ; 4. Tests d'utilisabilité (2) ; 5. Prototypage Figma (3) |
| Expérience | 3 à 5 ans, dont un projet audité RGAA |
| Arrivée | Dès la conception de la V1 complète, avant le développement des écrans hors POC |
| Écarts couverts | N° 3 (accessibilité), UX/UI. Ne couvre aucun écart technique |

## 6. Matrice cible

Situation après l'action de formation (Lead Dev à 3 en Kubernetes et en Helm) et l'arrivée des trois recrutements, avec les accompagnements externes. Seules les lignes avec un écart initial sont reprises. Le niveau cible de l'équipe est le meilleur niveau obtenu, recrutements compris. Les cellules de niveau sont des entiers.

**Règle de la criticité résiduelle.** Quand un écart subsiste, sa criticité baisse d'un cran (haute vers moyenne, moyenne vers basse) si l'écart restant est couvert par une pratique encadrée (binôme, revue de code) ou par un accompagnement externe. Sans cela, elle reste celle de la section 3. Une criticité basse ne baisse plus.

| Compétence | Requis | Max équipe aujourd'hui | Apport | Max cible | Écart résiduel | Criticité résiduelle |
| --- | --- | --- | --- | --- | --- | --- |
| Sécurité applicative, DevSecOps | 3 | 2 | DevOps (3) sur la chaîne de livraison ; test d'intrusion externe annuel | 3 | 0 | — |
| Kubernetes | 3 | 1 | Formation du Lead Dev (3) ; DevOps (4) | 4 | 0 | — |
| Helm | 3 | 1 | Formation du Lead Dev (3) ; DevOps (4) | 4 | 0 | — |
| RGAA 4.1 / WCAG 2.1 AA | 3 | 1 | UX/UI designer (3) | 3 | 0 | — |
| Observabilité | 3 | 1 | DevOps (3) | 3 | 0 | — |
| PostgreSQL : exploitation | 3 | 2 | DevOps (3) | 3 | 0 | — |
| GitHub Actions, GitOps | 3 | 2 | DevOps (3) | 3 | 0 | — |
| RabbitMQ, événementiel | 3 | 2 | DevOps (3) en exploitation | 3 | 0 | — |
| Charge (Locust) | 3 | 2 | QA (3) | 3 | 0 | — |
| Playwright, Vitest | 3 | 2 | QA (3) | 3 | 0 | — |
| UX/UI | 3 | 2 | UX/UI designer (3) | 3 | 0 | — |
| WebSocket (chat) | 3 | 2 | Pratique de Dev 1 en binôme, revue du Lead Dev | 2 | 1 | Basse (pratique encadrée) |
| OIDC, OAuth 2.0, JWT | 3 | 2 | Pratique des développeurs, revue de code | 2 | 1 | Basse (pratique encadrée) |
| Keycloak | 3 | 1 | DevOps (2) | 2 | 1 | Moyenne |
| RGPD | 3 | 1 | Accompagnement externe ponctuel | 1 | 2 | Basse (couverte par l'externe) |
| PCI DSS (SAQ A) | 2 | 1 | Accompagnement externe ponctuel | 1 | 1 | Basse (couverte par l'externe) |
| Intégration du PSP | 2 | 1 | Support d'intégration du PSP et audit externe | 1 | 1 | Basse (couverte par l'externe) |
| Produit, agilité | 3 | 2 | Aucun, rôle tenu par la direction | 2 | 1 | Basse |

**Synthèse.** Les écarts de criticité haute sont couverts : sécurité applicative (DevOps et test d'intrusion externe), Kubernetes et Helm (formation interne permanente et DevOps), accessibilité (UX/UI designer). Il reste des écarts moyens ou bas, acceptés : ils ne bloquent ni la livraison ni une exigence explicite. Le plus important, Keycloak (moyenne), est suivi par le Lead Dev. Le RGPD, PCI DSS et le PSP sont couverts hors équipe par des accompagnements externes.

## 7. Suite : plan de formation

L'action de formation détaillée sur Kubernetes et Helm (objectifs, durée, modalités, évaluation des acquis) est décrite dans le document `plan-formation.md` (à venir, tâche P2-06). Elle cible l'écart n° 2 de la section 4.
