# Glossaire de la soutenance

Les termes à employer **exactement** devant un jury technique. Chaque ligne donne une définition en une ou deux phrases et, quand il y en a un, l'endroit où le terme apparaît dans le POC. Les questions probables sont dans [questions.md](questions.md) ; les numéros L (limites) et PA (actions du plan) renvoient à l'[architecture du POC](../02-architecture/architecture-poc.md#8-limites-assumées-du-poc) et au [plan de remédiation](../06-securite/plan-remediation.md).

## Kubernetes et déploiement

| Terme | Définition | Dans le POC |
| --- | --- | --- |
| **Orchestrateur** | Logiciel qui place, surveille et recrée les conteneurs sur un ensemble de machines. | Kubernetes (k3s) : recrée un pod supprimé en 4,9 s sous charge ([protocole 5](../04-experimentations/05-charge-disponibilite/protocole.md)) |
| **k3s, k3d** | k3s est une distribution Kubernetes légère certifiée CNCF ; k3d fait tourner chaque nœud de k3s dans un conteneur Docker. | Cluster `collector` : 1 server et 2 agents, créé par `deploy/local/cluster.sh` ([ADR 0006](../02-architecture/adr/0006-kubernetes-local-k3d-argocd.md)) |
| **Nœud (server, agent)** | Machine du cluster. Le server porte le plan de contrôle (API, scheduler) ; les agents exécutent les pods. | Trois nœuds ; le server porte aussi des pods applicatifs ([architecture, section 2](../02-architecture/architecture-poc.md)) |
| **Pod** | Plus petite unité de Kubernetes : un ou plusieurs conteneurs qui partagent le réseau. | Un pod de `catalog-service` par réplica |
| **Réplica** | Copie d'un pod gérée par un Deployment. | 2 réplicas minimum par service, jusqu'à 5 avec l'HPA |
| **Deployment** | Objet qui maintient le nombre voulu de pods et remplace les anciens à chaque mise à jour. | Services et front, par le chart (`deploy/helm/collector-service/templates/deployment.yaml`) ; Keycloak |
| **StatefulSet** | Comme un Deployment, mais chaque pod garde un nom stable et son volume. | PostgreSQL et RabbitMQ (`deploy/infra`) |
| **Service (Kubernetes)** | Adresse réseau stable devant un ensemble de pods. | `keycloak.collector.svc.cluster.local:8080`, URL interne pour le JWKS |
| **Namespace** | Espace de noms qui regroupe des objets. | Un seul, `collector` |
| **Ingress, Traefik** | L'Ingress décrit comment le trafic externe entre dans le cluster ; Traefik est le contrôleur qui l'applique. | Traefik fourni par k3s, routage par hôte et chemin, HTTPS, `StripPrefix` ([ADR 0006](../02-architecture/adr/0006-kubernetes-local-k3d-argocd.md)) |
| **Chart Helm** | Paquet de modèles de manifestes Kubernetes, paramétré par des fichiers de valeurs (*values*). | Un chart générique pour les 2 services et le front (`deploy/helm/collector-service`) |
| **HPA** | *HorizontalPodAutoscaler* : ajuste le nombre de réplicas selon une métrique. | De 2 à 5 réplicas à 70 % de CPU ; fenêtre de stabilisation de 300 s à la descente |
| **Sonde liveness** | Contrôle périodique « le processus est-il vivant ? » ; un échec redémarre le conteneur. | `/health/live` |
| **Sonde readiness** | Contrôle « ce pod peut-il recevoir du trafic ? » ; un échec le retire du routage. | `/health/ready` (PostgreSQL seulement, jamais RabbitMQ) |
| **Requests et limits** | Ressources garanties (*requests*) et plafond (*limits*) d'un conteneur. | 100m CPU et 128 Mi demandés, 500m et 256 Mi au plus (`values.yaml`) ; l'HPA raisonne sur la requête CPU |
| **Secret Kubernetes** | Objet qui porte une donnée sensible ; encodé en base64, pas chiffré au repos par défaut. | Créés par `deploy.sh` à partir du `.env` local ; chiffrement au repos : PA-20 |
| **Auto-réparation** | Recréation automatique d'un pod défaillant ou supprimé. | 7,1 s sans charge ([protocole 4](../04-experimentations/04-deploiement/protocole.md)) |
| **Retour arrière (rollback)** | Retour à la révision précédente du déploiement (`helm rollback`). | Automatique si le déploiement échoue ; ne défait pas les migrations (L23) |
| **Opérateur, CRD** | Un opérateur est un programme qui gère une application dans Kubernetes ; une CRD ajoute un type d'objet à l'API. | Essayés puis abandonnés ([ADR 0008](../02-architecture/adr/0008-infrastructure-images-officielles.md)) ; seule exception, kube-prometheus-stack |
| **NetworkPolicy** | Règle qui limite les flux réseau entre pods. | Absente : L4, action PA-30 |
| **securityContext** | Réglages de sécurité d'un pod ou conteneur : utilisateur, système de fichiers en lecture seule, capacités Linux. | Appliqué aux services et au front ; pas à RabbitMQ ni à Keycloak (L17, L18) |
| **GitOps, Argo CD** | Le dépôt Git est la source de vérité ; Argo CD synchronise le cluster avec lui et détecte les dérives. | Cible seulement (L12, PA-52) |
| **cert-manager** | Composant qui émet et renouvelle automatiquement les certificats. | Cible (L11) ; le POC utilise un certificat mkcert |
| **mkcert, sslip.io** | mkcert génère une autorité et des certificats locaux de confiance ; sslip.io résout `*.127.0.0.1.sslip.io` vers `127.0.0.1`. | Certificat `*.127.0.0.1.sslip.io` chargé comme Secret TLS |

## Images et chaîne de livraison

| Terme | Définition | Dans le POC |
| --- | --- | --- |
| **CI/CD** | Intégration continue (construire et tester à chaque modification) et livraison continue (publier ce qui est validé). | GitHub Actions : `backend.yml` et `frontend.yml` ([cicd.md](../01-qualite/cicd.md)) |
| **Tag** | Étiquette lisible d'une image ; elle peut être déplacée. | `sha-<7 caractères du commit>`, jamais réécrit par la CI ; `main` est un repère mobile |
| **Digest** | Empreinte `sha256:…` calculée sur le contenu d'une image ; immuable. | `deploy.sh` déploie `tag@digest` après vérification sur GHCR ([cicd.md, traçabilité](../01-qualite/cicd.md#4-traçabilité)) |
| **GHCR** | *GitHub Container Registry* : registre d'images de GitHub. | `ghcr.io/luucaaas/<service>`, paquets publics |
| **Image multi-architecture** | Image publiée pour plusieurs processeurs sous un même tag. | amd64 et arm64, construites avec Buildx et QEMU |
| **Multi-stage** | Dockerfile en plusieurs étapes : on ne garde dans l'image finale que ce qui sert à l'exécution. | Images des services (base `python:3.12-slim`) et du front |
| **Quality gate** | Ensemble de conditions qu'une analyse doit remplir ; sinon le pipeline échoue. | SonarCloud ; démontrée en échec sur du code sans test ([conformité](../01-qualite/conformite-pipeline.md#4-preuves-de-blocage)) |
| **SonarCloud** | Service d'analyse statique de code et de mesure de qualité. | Un projet par service ; dette 0 min, duplication 0,0 % |
| **Trivy** | Scanner de vulnérabilités, de secrets et de configurations. | `--scanners vuln,secret --severity CRITICAL,HIGH --ignore-unfixed` ; binaire 0.76.0 vérifié par SHA-256 |

## Sécurité et identité

| Terme | Définition | Dans le POC |
| --- | --- | --- |
| **SAST** | Analyse statique du code source, sans l'exécuter. | SonarCloud |
| **SCA** | Analyse des dépendances et des paquets pour y trouver des vulnérabilités connues. | Trivy, `npm audit` |
| **DAST** | Analyse dynamique d'une application en fonctionnement. | OWASP ZAP, lancé ponctuellement ([rapport des scans](../06-securite/rapport-scans.md)) ; pas dans la CI (L13) |
| **CVE, CVSS** | Identifiant public d'une vulnérabilité ; échelle de gravité de 0 à 10. | Trivy les liste ; 201 lignes (89 CVE) sans correctif dans l'OS Debian |
| **`--ignore-unfixed`** | Option de Trivy qui écarte les vulnérabilités sans correctif publié. | Le blocage ne porte que sur ce qui est corrigeable |
| **DevSecOps, shift left** | Intégrer la sécurité à chaque étape du cycle plutôt que la contrôler à la fin ; détecter le plus tôt possible. | [Cycle en 8 étapes](../01-qualite/devsecops.md) |
| **STRIDE** | Classification des menaces : usurpation, falsification, répudiation, divulgation, déni de service, élévation de privilèges. | [Analyse de risques, section 3](../06-securite/analyse-risques.md#3-flux-frontières-de-confiance-et-stride) |
| **OWASP Top 10** | Liste des dix catégories de risques les plus courantes des applications web ; il existe une liste dédiée aux API. | Correspondance dans l'[analyse de risques, section 4](../06-securite/analyse-risques.md#4-correspondance-owasp) |
| **Criticité** | Impact (1 à 5) × probabilité (1 à 5) ; critique ≥ 15, élevé 10 à 14, moyen 5 à 9, faible ≤ 4. | 62 risques notés ([plan, méthode](../06-securite/plan-remediation.md#2-méthode-de-priorisation)) |
| **Risque résiduel** | Risque qui reste après les mesures existantes ou prévues. | Probabilité du registre = probabilité résiduelle ; critiques de 7 à 0 visé |
| **Plan de remédiation** | Liste priorisée d'actions qui réduisent les risques, avec responsable, effort et indicateur. | 58 actions, PA-01 à PA-58 |
| **OIDC, OAuth 2.0** | OAuth 2.0 délègue l'autorisation ; OpenID Connect y ajoute l'identité de l'utilisateur. | Keycloak, flux *Authorization Code* |
| **PKCE** | Extension qui lie la demande d'autorisation à l'échange du code par un secret à usage unique (RFC 7636). | Client public `collector-web`, méthode S256 |
| **JWT** | Jeton signé, composé d'un en-tête, d'une charge de revendications (*claims*) et d'une signature. | Jeton d'accès de 5 minutes |
| **Claims `iss`, `aud`, `exp`, `sub`** | Émetteur, destinataire, expiration et identifiant de l'utilisateur dans le jeton. | Les quatre sont exigés ; `aud` vaut `collector-api` |
| **JWKS** | Ensemble des clés publiques d'un serveur d'identité, publié à une URL. | Téléchargé par l'URL interne, mis en cache (600 s) |
| **RS256** | Signature RSA avec SHA-256 : la clé privée signe, la clé publique vérifie. | Seul algorithme accepté ; `none` et HS256 rejetés |
| **RBAC** | Contrôle d'accès par rôles. | `buyer`, `seller`, `admin`, vérifiés côté API |
| **TLS, HSTS** | TLS chiffre le trafic HTTPS ; HSTS ordonne au navigateur de n'utiliser que HTTPS. | TLS terminé par Traefik ; HSTS d'un an sur `api.` et `auth.` |
| **mTLS** | TLS dans les deux sens : chaque pod prouve son identité. | Absent : trafic interne en clair (L10, PA-55) |
| **CORS** | Mécanisme du navigateur qui décide quelles origines peuvent appeler une API. | Seule l'origine `https://app.127.0.0.1.sslip.io` est autorisée |
| **CSP** | *Content Security Policy* : en-tête qui liste les sources de scripts, styles et images autorisées. | `script-src 'self'` ; reste `style-src 'unsafe-inline'` (L24) |
| **XSS, BFF** | XSS : injection de script dans une page. BFF : serveur intermédiaire qui garde les jetons et ne donne au navigateur qu'un cookie `HttpOnly`. | Jetons en mémoire ; BFF dans la cible (L5, PA-56) |

## Messagerie et fiabilité

| Terme | Définition | Dans le POC |
| --- | --- | --- |
| **Broker, exchange, file (queue)** | Le broker reçoit les messages ; l'exchange les route vers des files ; chaque consommateur lit sa file. | RabbitMQ ; exchange `topic` `article.events`, file `notification.article-events` |
| **Liaison (binding)** | Règle qui relie une file à un exchange par un motif de clé de routage. | `article.*` ; un nouveau consommateur se branche par une liaison |
| **Événement transportant l'état** | L'événement contient les données utiles : le consommateur n'a pas à rappeler le producteur. | Catégorie, vendeur, titre, prix |
| **At-least-once** | Garantie « au moins une fois » : un message peut être livré plusieurs fois, jamais perdu une fois confirmé. | 1 message relivré sur 1 000, 0 doublon traité |
| **Idempotence** | Une opération répétée donne le même état. | `UNIQUE (user_id, source_event_id)` et `ON CONFLICT DO NOTHING` ; `PUT` du prix |
| **Acquittement, publisher confirm** | Le consommateur acquitte un message traité ; le producteur attend la confirmation du broker. | Acquittement après le commit ; publication avec confirmation |
| **Outbox** | L'événement est écrit en base dans la transaction métier, puis publié par un relais. | Absente : L2, action PA-54 |
| **DLQ, quorum queue** | File des messages en échec ; file répliquée par consensus (Raft). | Absentes : L7, action PA-54 |
| **Cohérence à terme** | Les données de plusieurs services convergent après un court délai. | Notification en moins de 0,1 s |

## Qualité et tests

| Terme | Définition | Dans le POC |
| --- | --- | --- |
| **ISO 25010** | Norme qui décompose la qualité logicielle en caractéristiques (maintenabilité, fiabilité, sécurité…). | Chaque indicateur I1 à I5 y est rattaché ([indicateurs](../01-qualite/indicateurs.md)) |
| **p95** | Durée sous laquelle 95 % des requêtes se terminent. | 21 ms en lecture, 23 ms en publication à 50 utilisateurs |
| **Couverture de lignes, de branches** | Part des lignes exécutées par les tests ; part des alternatives (`if`, `else`) exécutées. | 98,45 % et 97,66 % combinées ; branches 94,17 % et 91,49 % |
| **Dette technique** | Coût futur des raccourcis pris dans le code ou l'outillage. | 0 min pour SonarCloud, mais 531 lignes dupliquées entre services |
| **Test d'intégration** | Teste le code avec une vraie dépendance. | testcontainers : PostgreSQL et RabbitMQ jetables |
| **Test d'acceptation** | Prouve qu'un critère de la user story est satisfait de bout en bout. | 17 tests pytest + httpx, un par critère |
| **Test de non-régression** | Rejeu de la suite pour vérifier qu'une modification n'a rien cassé. | Toute la suite à chaque push |
| **Locust, Playwright, Vitest** | Locust : tests de charge ; Playwright : parcours dans un navigateur ; Vitest : tests de composants du front. | Locust et Playwright hors CI ; 62 tests Vitest |
| **RFC 9457** | Format standard d'erreur HTTP (*Problem Details*). | Réponses `application/problem+json` |
| **`correlation_id`** | Identifiant qui suit une requête dans les logs et les événements. | Repris de `X-Request-ID` s'il est valide (128 caractères au plus) |

## Gestion de projet et décisions

| Terme | Définition | Dans le POC |
| --- | --- | --- |
| **POC** | Preuve de faisabilité : le plus petit prototype qui valide les points d'architecture risqués. | Chaîne publier, contrôler, notifier ([ADR 0007](../02-architecture/adr/0007-simplification-perimetre-poc.md)) |
| **ADR** | *Architecture Decision Record* : décision d'architecture avec son contexte, ses options et ses conséquences. | [ADR 0001 à 0008](../02-architecture/adr/README.md) |
| **RACI** | Tableau des rôles : réalise, rend des comptes, consulté, informé. | [Processus de test](../01-qualite/processus-test.md#raci) |
| **Modèle de Kirkpatrick** | Évaluation d'une formation à quatre niveaux : réaction, apprentissage, comportement, résultats. | [Plan de formation](../05-competences/plan-formation.md#7-évaluation-modèle-de-kirkpatrick) |
