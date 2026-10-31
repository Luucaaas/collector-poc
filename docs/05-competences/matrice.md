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
| Back-end | Python 3.12, FastAPI, Pydantic v2 | 3 | 3 | 3 | 1 | 3 | 0 | — |
| Back-end | SQLAlchemy 2.0, Alembic | 3 | 2 | 3 | 1 | 3 | 0 | — |
| Front | React, TypeScript, Vite | 3 | 1 | 1 | 3 | 3 | 0 | — |
| Front | MUI, React Router, react-oidc-context | 2 | 1 | 0 | 3 | 3 | 0 | — |
| Données | PostgreSQL : modèle, index, droits par utilisateur | 3 | 2 | 3 | 2 | 3 | 0 | — |
| Données | PostgreSQL : exploitation (sauvegardes, réplication) | 3 | 1 | 2 | 1 | 2 | 1 | Moyenne |
| Messagerie | RabbitMQ, aio-pika, architecture événementielle (outbox, DLQ) | 3 | 2 | 2 | 1 | 2 | 1 | Moyenne |
| Identité | OIDC, OAuth 2.0, JWT (PKCE, JWKS, audiences) | 3 | 2 | 2 | 2 | 2 | 1 | Moyenne |
| Identité | Keycloak : realm, rôles, fédération Entra ID | 3 | 1 | 1 | 0 | 1 | 2 | Moyenne |
| Conteneurs | Docker : images multi-stage, non-root, multi-architecture | 3 | 2 | 3 | 2 | 3 | 0 | — |
| Orchestration | Kubernetes : déploiement, sondes, HPA, ingress Traefik, TLS | 3 | 1 | 1 | 0 | 1 | 2 | Haute |
| Orchestration | Helm : chart, values, secrets | 3 | 1 | 0 | 0 | 1 | 2 | Haute |
| CI/CD | GitHub Actions, GHCR, GitOps (Argo CD en cible) | 3 | 1 | 2 | 2 | 2 | 1 | Moyenne |
| Observabilité | Prometheus, Grafana, logs JSON corrélés, alertes | 3 | 1 | 1 | 0 | 1 | 2 | Moyenne |
| Tests | pytest, pytest-cov, testcontainers, tests d'acceptation httpx | 3 | 3 | 3 | 2 | 3 | 0 | — |
| Tests | Test de charge (Locust) et analyse des résultats | 3 | 2 | 2 | 1 | 2 | 1 | Moyenne |
| Tests | Vitest, Playwright (tests front et de bout en bout) | 3 | 1 | 1 | 2 | 2 | 1 | Moyenne |
| Sécurité | Sécurité applicative, DevSecOps, OWASP (Ruff, SonarCloud, Trivy, ZAP) | 3 | 2 | 2 | 2 | 2 | 1 | Moyenne |
| Conformité | RGPD : base légale, consentement, durées, droits des personnes | 3 | 1 | 1 | 1 | 1 | 2 | Moyenne |
| Conformité | PCI DSS par délégation au PSP (périmètre SAQ A) | 2 | 1 | 1 | 1 | 1 | 1 | Moyenne |
| Conformité | Accessibilité RGAA / WCAG 2.2 | 3 | 1 | 0 | 1 | 1 | 2 | Haute |
| Conformité | Internationalisation (i18n) | 2 | 0 | 1 | 2 | 2 | 0 | — |
| UX/UI | Conception d'interface, parcours, design system | 3 | 1 | 0 | 2 | 2 | 1 | Moyenne |
| Produit | Gestion de produit, agilité (backlog, user stories, revues) | 3 | 2 | 1 | 2 | 2 | 1 | Basse |

Justification de quelques niveaux.

- **Lead Dev : Python à 3, le reste de la stack à 1 ou 2.** Il maîtrise Python. En React/TypeScript, Kubernetes, Helm et GitHub Actions, il n'a que des notions : niveau 1 à chaque fois. Il n'est pas à 4 en Python faute de référence sur plusieurs projets en production.
- **Dev 2, React à 3 et non 4.** Cinq ans de front en agence donnent la maîtrise, pas la référence sur l'architecture d'une SPA complexe.
- **Aucune cellule à 4 dans l'équipe actuelle.** Cinq ans d'expérience ne font pas d'expert : le niveau 4 s'obtient par un recrutement spécialisé.
- **PCI DSS à 2 requis.** Collector délègue la saisie de la carte au PSP et ne voit qu'un jeton. Il faut comprendre le périmètre et ses obligations, pas auditer un environnement de cartes.
- **Produit et agilité à 3.** Le rôle de Product Owner est tenu par un·e des deux dirigeant·e·s (anciens chefs de projet IT), ce qui limite la criticité de l'écart.

## 4. Analyse des écarts

Les cinq écarts les plus critiques, par ordre de priorité.

| N° | Écart | Risque pour le projet | Réponse retenue |
| --- | --- | --- | --- |
| 1 | Kubernetes et Helm (requis 3, max 1, criticité haute) | La mise en production, la montée en charge et la reprise après incident dépendent d'un outil que personne ne maîtrise. Le POC repose sur un chart et un cluster : sans compétence, le Lead Dev ne peut ni les défendre ni les faire évoluer | **Formation** de l'équipe, en priorité du Lead Dev (niveau 3), puis **recrutement** d'un DevOps/SRE pour l'exploitation de production (niveau 4) |
| 2 | Accessibilité RGAA / WCAG (requis 3, max 1, criticité haute) | L'accessibilité est une exigence explicite du contexte. Sans référent, l'interface est livrée non conforme et la correction après coup coûte plus cher que de concevoir accessible | **Recrutement** d'un·e UX/UI designer avec compétence accessibilité. Le niveau 3 se vérifie sur plusieurs projets, il ne s'acquiert pas en quelques semaines |
| 3 | Observabilité et exploitation (Prometheus, Grafana, PostgreSQL exploité ; requis 3, max 1 ou 2) | Une panne ou une dégradation passe inaperçue. Sans sauvegarde testée, une perte de données est irréversible | **Recrutement** du DevOps/SRE (écart commun avec le n° 1), appuyé par une formation de base du Lead Dev |
| 4 | Qualité des tests de charge et de bout en bout (Locust, Playwright ; requis 3, max 2) | Les tests de charge et les parcours front sont écrits par des développeurs qui ne sont pas spécialistes : couverture incomplète, tests fragiles, validation de l'acceptation faite par ceux qui codent | **Recrutement** d'un·e QA automaticien·ne, qui reprend la revue des tests et la validation de l'acceptation |
| 5 | Conformité RGPD et PCI DSS (RGPD requis 3, max 1 ; PCI DSS requis 2, max 1) | Traitement de données personnelles d'acheteurs et de vendeurs sans base légale établie, sanction de la CNIL, atteinte à la confiance. Une erreur de périmètre PCI DSS engage la responsabilité de Collector | **Accompagnement externe ponctuel** : un·e DPO ou un cabinet de conformité pour le registre et l'analyse d'impact, un audit du périmètre PCI DSS avant l'ouverture |

Choix entre formation, recrutement et accompagnement externe.

| Critère | Formation | Recrutement | Accompagnement externe |
| --- | --- | --- | --- |
| Durée d'acquisition | Quelques semaines pour passer de 1 à 2 ou 3 avec de la pratique. Quelques années pour atteindre 4 | Le niveau 4 est acquis dès l'arrivée, après 2 à 4 mois de recrutement | Immédiate |
| Besoin | Permanent et au cœur du métier de l'équipe | Permanent, mais demandant un métier à plein temps | Ponctuel (audit, analyse d'impact) |
| Retenu pour | Kubernetes et Helm, au niveau 3 : le Lead Dev doit pouvoir superviser, relire un chart et diagnostiquer, sans dépendre d'une seule personne | DevOps, QA, UX/UI : des métiers distincts, à temps plein | RGPD, PCI DSS : peu de jours par an |

**Écart ciblé par l'action de formation.** L'action de formation détaillée (à venir, `plan-formation.md`) vise **Kubernetes et Helm**. C'est l'écart de criticité haute que l'équipe doit maîtriser en interne en permanence : le Lead Dev supervise le déploiement et doit défendre le cluster, même une fois le DevOps arrivé. L'écart d'accessibilité, également de criticité haute, est traité par un recrutement : il demande un métier de conception et non une formation de quelques semaines.

## 5. Recrutements envisagés

Trois profils, qui s'articulent avec le RACI de `docs/01-qualite/processus-test.md` : le QA reprend la revue des tests et la validation de l'acceptation, le DevOps reprend l'exécution de la CI et du déploiement. Aucun Product Owner n'est recruté : le rôle est tenu par un·e dirigeant·e.

### 5.1 Ingénieur DevOps / SRE

| Rubrique | Contenu |
| --- | --- |
| Missions | Exploiter le Kubernetes managé de production. Faire évoluer les charts Helm et la CI/CD (GitHub Actions, puis Argo CD). Mettre en place l'observabilité et les alertes. Gérer les sauvegardes et la réplication PostgreSQL. Animer les astreintes |
| Compétences clés | 1. Kubernetes (niveau 4) ; 2. Helm et GitOps (4) ; 3. Observabilité Prometheus/Grafana (3) ; 4. GitHub Actions et sécurité de la chaîne de livraison (3) ; 5. Exploitation PostgreSQL et RabbitMQ en cluster (3) |
| Expérience | 4 à 6 ans en exploitation ou en plateforme, dont au moins 2 ans sur Kubernetes en production |
| Arrivée | Après le POC, avant la migration vers le Kubernetes managé européen et la première mise en production |
| Écarts couverts | N° 1 (Kubernetes, Helm), n° 3 (observabilité, exploitation PostgreSQL), et en partie GitHub Actions et sécurité applicative |

### 5.2 QA automaticien·ne

| Rubrique | Contenu |
| --- | --- |
| Missions | Définir la stratégie de test avec le Lead Dev. Écrire et maintenir les tests d'acceptation, de bout en bout (Playwright) et de charge (Locust). Revoir les tests des développeurs. Valider l'acceptation avec le Product Owner. Suivre les indicateurs qualité |
| Compétences clés | 1. Playwright et tests de bout en bout (niveau 3) ; 2. Locust et analyse de performance (3) ; 3. pytest et tests d'API (3) ; 4. Conception de cas de test et gestion des anomalies (3) ; 5. Intégration des tests en CI (2) |
| Expérience | 3 à 5 ans en automatisation de tests |
| Arrivée | Dès le premier sprint après le POC, avant la montée en charge de l'équipe de développement |
| Écarts couverts | N° 4 (charge, bout en bout). Ne couvre ni Kubernetes ni l'accessibilité |

### 5.3 UX/UI designer avec compétence accessibilité

| Rubrique | Contenu |
| --- | --- |
| Missions | Concevoir les parcours acheteur, vendeur et back-office, et le design system. Porter l'accessibilité RGAA/WCAG dès la conception. Auditer les écrans livrés. Définir les règles d'internationalisation de l'interface |
| Compétences clés | 1. Conception d'interface et parcours (niveau 3) ; 2. Design system (3) ; 3. RGAA / WCAG 2.2 (3) ; 4. Tests d'utilisabilité (2) ; 5. Prototypage Figma (3) |
| Expérience | 3 à 5 ans, dont un projet audité RGAA |
| Arrivée | Dès la conception de la V1 complète, avant le développement des écrans hors POC |
| Écarts couverts | N° 2 (accessibilité), UX/UI. Ne couvre aucun écart technique |

## 6. Matrice cible

Situation après l'action de formation (Lead Dev à 3 en Kubernetes et en Helm) et l'arrivée des trois recrutements. Seules les lignes avec un écart initial sont reprises. Le niveau cible de l'équipe est le meilleur niveau obtenu, recrutements compris.

| Compétence | Requis | Max équipe aujourd'hui | Apport | Max cible | Écart résiduel | Criticité résiduelle |
| --- | --- | --- | --- | --- | --- | --- |
| Kubernetes | 3 | 1 | Formation du Lead Dev (3) ; DevOps (4) | 4 | 0 | — |
| Helm | 3 | 1 | Formation du Lead Dev (3) ; DevOps (4) | 4 | 0 | — |
| RGAA / WCAG | 3 | 1 | UX/UI designer (3) | 3 | 0 | — |
| Observabilité | 3 | 1 | DevOps (3) | 3 | 0 | — |
| PostgreSQL : exploitation | 3 | 2 | DevOps (3) | 3 | 0 | — |
| GitHub Actions, GitOps | 3 | 2 | DevOps (3) | 3 | 0 | — |
| Charge (Locust) | 3 | 2 | QA (3) | 3 | 0 | — |
| Playwright, Vitest | 3 | 2 | QA (3) | 3 | 0 | — |
| Sécurité applicative, DevSecOps | 3 | 2 | DevOps (3) sur la chaîne de livraison | 3 | 0 | — |
| UX/UI | 3 | 2 | UX/UI designer (3) | 3 | 0 | — |
| RabbitMQ, événementiel | 3 | 2 | DevOps (2) en exploitation, pratique de Dev 1 | 2 | 1 | Basse |
| OIDC, OAuth 2.0, JWT | 3 | 2 | Pratique des développeurs | 2 | 1 | Basse |
| Keycloak | 3 | 1 | DevOps (2) | 2 | 1 | Moyenne |
| RGPD | 3 | 1 | Accompagnement externe ponctuel | 1 (équipe) | 2 | Moyenne, couverte par l'externe |
| PCI DSS (SAQ A) | 2 | 1 | Accompagnement externe ponctuel | 1 (équipe) | 1 | Basse, couverte par l'externe |
| Produit, agilité | 3 | 2 | Aucun, rôle tenu par la direction | 2 | 1 | Basse |

**Synthèse.** Les deux écarts de criticité haute sont couverts : Kubernetes et Helm (formation interne permanente et DevOps) et accessibilité (UX/UI designer). Il reste des écarts moyens ou bas, acceptés : ils ne bloquent ni la livraison ni une exigence explicite. Les plus importants, Keycloak et RGPD, sont suivis par le Lead Dev. Le RGPD est couvert hors équipe par un accompagnement externe.

## 7. Suite : plan de formation

L'action de formation détaillée sur Kubernetes et Helm (objectifs, durée, modalités, évaluation des acquis) est décrite dans le document `plan-formation.md` (à venir, tâche P2-06). Elle cible l'écart n° 1 de la section 4.
