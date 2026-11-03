# 04 — Expérimentations en bac à sable

Un protocole par technologie testée. Chaque dossier contient le protocole (`protocole.md`), le script qui le rejoue (`run.sh`) et le code ou les manifestes nécessaires. Un protocole n'est pas un guide d'installation : il pose une question, mesure, constate les limites et aboutit à une décision.

## Index

| N° | Expérimentation | Dossier | Exécution de référence | Décision |
| --- | --- | --- | --- | --- |
| 1 | RabbitMQ sur Kubernetes (k3d, image officielle, StatefulSet, sans opérateur) | [01-rabbitmq](01-rabbitmq/protocole.md) | 03/11/2026 18:55 | Adoptée (0 message perdu sur 2 × 1 000, retour à Ready du broker en 10 s au lieu de 54 s avec l'opérateur, abandonné) |
| 2 | Keycloak + Traefik + certificat mkcert (images officielles, sans opérateur) | [02-keycloak-tls](02-keycloak-tls/protocole.md) | 03/11/2026 18:29 | Adoptée (validation locale des JWT, 15 cas d'autorisation conformes ; PKCE et rotation des clés à tester avec le front) |
| 3 | Observabilité : kube-prometheus-stack (Prometheus, Grafana) sur k3d | [03-observabilite](03-observabilite/protocole.md) | 02/11/2026 22:43 | Adoptée en version allégée (environ 600 Mi ; bornes d'histogramme à définir pour le p95) |
| 4 | (option) Kafka | non réalisée | non réalisée | Écartée (journal des décisions du 02/11/2026), rejeté par l'ADR 0003 |

## Modèle commun des protocoles

Chaque `protocole.md` suit les 8 rubriques ci-dessous, dans cet ordre.

1. **Objectif et question posée** : ce qu'on veut prouver, formulé comme une question à laquelle l'expérience répond par oui ou non.
2. **Technologies testées et interactions** : composants en jeu et leurs échanges (schéma Mermaid court si utile).
3. **Environnement** : machine, système, Docker (CPU, mémoire), versions **exactes** de chaque outil, image et chart.
4. **Étapes reproductibles** : la commande unique (`run.sh`) et ce que fait chaque étape.
5. **Résultats mesurés** : tableau des valeurs réelles de la dernière exécution, avec sa date.
6. **Difficultés rencontrées et solutions** : ce qui a posé problème, comment c'est résolu.
7. **Limites de l'expérimentation** : ce que l'expérience ne prouve pas.
8. **Décision** : adoption, rejet ou conditions, avec renvoi vers l'ADR concernée.

Règles communes :

- Tout se rejoue par script, sur un cluster k3d jetable, supprimé à la fin (option `--keep` pour le conserver).
- Les versions sont figées, d'un tag précis et publié depuis plusieurs semaines. Aucun chart ni image Bitnami : l'infrastructure s'installe avec les **images officielles des éditeurs** et des manifestes simples, sans opérateur, sans CRD ajoutée et sans cert-manager ([ADR 0008](../02-architecture/adr/0008-infrastructure-images-officielles.md)). Seule exception, kube-prometheus-stack, installé par son chart Helm.
- Aucun secret dans le dépôt : les identifiants sont **générés par `run.sh`** (module `secrets` de Python), écrits dans des Secrets Kubernetes ou dans `.local/` (ignoré par Git), et jamais affichés. Seule exception, le mot de passe de Grafana, généré par le chart et lu dans le Secret `kps-grafana`.
- Le code de bac à sable est vérifié par Ruff et mypy, sans tests unitaires : ce n'est pas une fonctionnalité du POC.

## Synthèse et conséquences pour le POC

Les trois expérimentations ont répondu par oui, avec des conditions. L'infrastructure du POC s'installe donc à partir des images officielles, par des manifestes simples ([ADR 0008](../02-architecture/adr/0008-infrastructure-images-officielles.md)), à une exception près (kube-prometheus-stack). Chaque ligne ci-dessous donne la décision, sa source (protocole et section) et la phase qui l'applique. Les chiffres sont ceux des protocoles ; un calcul fait ici est signalé comme tel.

Rappel des phases : 4 = services, 5 = CI, 6 = déploiement, 7 = front, 8 = tests de charge et démonstration de disponibilité.

### À appliquer dans les services (phase 4)

| Décision | Source | Phase |
| --- | --- | --- |
| **Publier avec confirmation du broker, et réessayer.** À la suppression de son pod, le broker est de nouveau prêt 9,995 s plus tard ; le producteur a vu une indisponibilité de 10,547 s et republié 21 fois, jusqu'à la confirmation. Sans *outbox*, un événement non confirmé est perdu (limite L2) | protocole 1, §5, §8 | 4 |
| **Doublons couverts par `UNIQUE (user_id, source_event_id)`** : la livraison est « au moins une fois » (1 message relivré sur 1 000 en A et en B, 0 doublon traité) | protocole 1, §5, §8 | 4 |
| **Règle d'échec** : remise en file une fois, puis rejet journalisé (message empoisonné traité 2 fois, 99 messages sains traités sur 99, sans blocage) | protocole 1, §5 (scénario C) | 4 |
| **Gestionnaire de SIGTERM** (ou init) dans les images Python : un Python en PID 1 n'applique pas l'action par défaut de SIGTERM. Cause probable, non vérifiée ; mesure exploratoire non conservée : l'ancien pod a travaillé 9,808 s après la suppression. À vérifier sur l'image réelle d'un service | protocole 1, §6, §8 | 4 |
| **Sonde `/health/ready` sans RabbitMQ** : la reconnexion automatique d'aio-pika (`connect_robust`) suffit | protocole 1, §8 | 4 |
| **Validation du JWT** : RS256 imposé (cas 12 : l'algorithme `none` est rejeté), `iss` comparé à l'URL publique, `aud = collector-api` (cas 8), `exp` (cas 15) ; clés JWKS récupérées par l'URL interne et mises en cache (600 s, rechargement au plus une fois par 30 s sur un `kid` inconnu) ; 1 seul appel JWKS pour 216 requêtes. 15 cas d'autorisation sur 15 conformes | protocole 2, §2, §5 (mesures 3 à 5), §8 | 4 |
| **Un seul titre pour tous les 401** (« Non authentifié ») : la raison du rejet reste dans les logs, jamais dans la réponse | protocole 2, §5 (mesure 3) ; journal des décisions du 03/11/2026 | 4 |
| **`X-Request-ID` borné et validé** : l'API de bac à sable le reprend tel quel. Règle du POC : repris s'il fait au plus 128 caractères de `[A-Za-z0-9._-]`, sinon un UUID est généré | [fiche P3-03](../suivi/taches/P3-03.md#décision-finale-du-chef) (décision finale, contre-vérification du chef) ; `contrats.md` §1.3 | 4 |
| **Vérifier le type de `realm_access`** : un jeton signé mais mal formé donnerait une erreur 500 | [fiche P3-03](../suivi/taches/P3-03.md#décision-finale-du-chef) (décision finale, contre-vérification du chef) | 4 |
| **JWKS mal formé : répondre 503**, pas 500 | [fiche P3-03](../suivi/taches/P3-03.md#décision-finale-du-chef) (décision finale, contre-vérification du chef) | 4 |
| **Bornes d'histogramme alignées sur les seuils d'I3** (300 et 500 ms) : avec les bornes par défaut de l'instrumentator (0,1 / 0,5 / 1 s), un p95 de 200 ms est lu à 0,4800 s (+140 %) ; avec des bornes serrées, 0,2474 s (+23,7 %) | protocole 3, §5, §7, §8 | 4 |
| **Champ `correlation_id`** dans les logs JSON, valeur de `X-Request-ID` (vérifié : même valeur dans l'en-tête et dans le log) ; même nom dans les événements | protocole 3, §5 (journaux) ; journal des décisions du 02/11/2026 | 4 |

### À appliquer au déploiement (phase 6)

| Décision | Source | Phase |
| --- | --- | --- |
| **Manifestes de l'infrastructure dans `deploy/infra`** : PostgreSQL (`postgres:18.4-alpine`, StatefulSet d'un réplica), RabbitMQ (`rabbitmq:4.3.5-management`, StatefulSet, Services dont un *headless*), Keycloak (`quay.io/keycloak/keycloak:26.8.0`) ; values de kube-prometheus-stack 91.9.0. Secrets générés par script | ADR 0008 ; protocoles 1 à 3, §2 et §3 | 6 |
| **Un utilisateur PostgreSQL par service, sans droit de superutilisateur**, de création de base ni de rôle, propriétaire de sa seule base (vérifié pour le rôle `keycloak`) | protocole 2, §2, §5 (PostgreSQL), §8 | 6 |
| **`securityContext` explicite pour Keycloak et PostgreSQL** (à faire : absent des manifestes de bac à sable) | [fiche P3-03](../suivi/taches/P3-03.md#décision-finale-du-chef) (décision finale, contre-vérification du chef) ; limite L17 | 6 |
| **Broker : ne pas poser de `fsGroup`** (le nœud refuse de démarrer à la recréation du pod : cookie Erlang lisible par le groupe). Le broker démarre en root ; durcissement à étudier | protocole 1, §6, §7, §8 ; limite L18 | 6 |
| **Sondes de RabbitMQ par `rabbitmq-diagnostics`** : *readiness* `check_port_connectivity` (période 5 s), *liveness* `ping` (délai initial 60 s, 6 échecs de 30 s), `terminationGracePeriodSeconds: 60`. La période de 5 s coûte environ 3,4 s sur les 10 s de retour à Ready | protocole 1, §2, §5 | 6 |
| **Ressources de RabbitMQ** : requête de 200m CPU, 512 Mi de mémoire en requête et en limite (consommation mesurée : 135 Mi) | protocole 1, §8 | 6 |
| **Keycloak** : sondes en HTTP sur le port 9000, `KC_HOSTNAME` en URL complète, `KC_PROXY_HEADERS=xforwarded`, `iss` validé avec l'URL publique et clés récupérées par l'URL interne | protocole 2, §2, §6, §7 | 6 |
| **Realm du POC** : reprendre les *client scopes* `roles`, `basic`, `web-origins`, `acr` et le scope d'audience `collector-api` ; ne pas reprendre les trois clients de test | protocole 2, §6, §8 | 6 |
| **Routage par `/<service>/api/v1`** avec `StripPrefix` : `/health/*` et `/metrics` restent hors de l'ingress (cas 13 : 404) | protocole 2, §5 (cas 13), §8 | 6 |
| **TLS** : certificat mkcert en Secret TLS, `TLSStore` par défaut, redirection 80 vers 443 par `HelmChartConfig` (301). Hôtes `app.`, `api.`, `auth.`, `grafana.127.0.0.1.sslip.io` | protocole 2, §2, §5 (mesures 1 et 2) | 6 |
| **kube-prometheus-stack allégé** : kube-state-metrics et collecte du kubelet gardés ; Alertmanager, règles par défaut, node-exporter, webhooks et TLS de l'opérateur désactivés ; `serviceMonitorSelectorNilUsesHelmValues: false`, rétention de 2 h, `ServiceMonitor` à 15 s (délai de visibilité de 3,69 s à 13,12 s sur 5 essais), tableaux de bord chargés par le sidecar depuis une ConfigMap | protocole 3, §2, §5, §8 | 6 |

### Budget mémoire et disque (phase 6)

Mémoire relevée par `kubectl top pods` (au repos pour les expérimentations 2 et 3, en fin d'exécution pour la 1), dans trois clusters distincts : jamais ensemble. La somme est un **calcul** fait ici :

| Composant | Mémoire | Source |
| --- | --- | --- |
| RabbitMQ (broker) | 135 Mi | protocole 1, §5 |
| Keycloak | 581 Mi | protocole 2, §5 (mesure 6) |
| PostgreSQL | 56 Mi | protocole 2, §5 (mesure 6) |
| Traefik | 25 Mi | protocole 2, §5 (mesure 6) |
| kube-prometheus-stack (Grafana avec sidecars 403 Mi, Prometheus 164 Mi, opérateur 17 Mi, kube-state-metrics 16 Mi) | 600 Mi | protocole 3, §5 |
| **Somme (calcul)** | **1 397 Mi** | 135 + 581 + 56 + 25 + 600 |

- La mémoire de Docker Desktop est de 8 322 555 904 octets, soit 7 937 Mi (calcul) : la somme représente environ 17,6 % (calcul).
- **URL interne de Keycloak** : celle du POC est `http://keycloak.collector.svc.cluster.local:8080` (`contrats.md` §1.2). L'expérimentation 2 utilisait `keycloak-service.keycloak.svc` (nommage hérité de l'opérateur, namespace `keycloak`) : à ne pas reprendre en phase 6.
- **Non mesuré** : les deux services du POC (2 à 5 réplicas chacun avec l'HPA), le front, le consommateur, le plan de contrôle de k3s (les `kubectl top nodes` des expérimentations 2 et 3 donnent 873 + 255 + 890 = 2 018 Mi (calcul) et 1 064 + 281 + 957 = 2 302 Mi (calcul), en additionnant les trois nœuds ; ces totaux contiennent le système et k3s, dans des clusters qui n'ont pas les mêmes composants), les pics (un relevé « au repos » et un après les mesures seulement) et le démarrage de Keycloak (non mesuré). **Le total du POC complet n'est pas connu : il se mesure en phase 6**, avec `kubectl top pods -A` et `kubectl top nodes` sur le déploiement complet.
- **Disque libre** : une exécution consomme 1,5 Go (expérimentation 1, seuil de départ du script : 5 000 Mo), 3,7 Go (expérimentation 2, 7 Go) et 3,7 Go (expérimentation 3, 7 Go). Le kubelet évince les pods sous environ 3,1 Go libres (valeur relevée à l'expérimentation 3, non remesurée depuis). La consommation du POC complet n'est pas mesurée et ne se déduit pas de ces trois valeurs (relevées sur des états différents de la VM Docker). Seuil de départ proposé pour `check-tools.sh` et `deploy.sh` : 7 Go libres, le plus élevé des trois, à remplacer par la mesure du déploiement complet.

### À tester plus tard

| Point | Source | Phase |
| --- | --- | --- |
| **Flux PKCE dans un navigateur** et redirections du client public `collector-web` : défini dans le realm, jamais exercé (confirmation de l'ADR 0004) | protocole 2, §7, §8 | 7 |
| **Panneau « réplicas » et sommes sur plusieurs pods avec l'HPA** : mesuré avec un seul réplica ; le panneau lit le Deployment, pas l'HPA | protocole 3, §7 | 8 |
| **Crash brutal du broker** (arrêt sans vidage des données) : seul l'arrêt propre (SIGTERM) est testé | protocole 1, §7 | à planifier |
| **Rotation des clés de Keycloak** (rechargement du JWKS sur `kid` inconnu après plus de 30 s, expiration du cache de 600 s) | protocole 2, §7 | à planifier |
| **Aspect visuel du tableau de bord Grafana** : chargement et requêtes vérifiés, pas l'affichage | protocole 3, §7 | 8 |

### Ce qui reste dans la cible

Opérateurs (RabbitMQ Cluster Operator, CloudNativePG, Keycloak Operator) et cert-manager ; RabbitMQ en cluster de 3 nœuds avec *quorum queues* et DLQ (L7) ; PostgreSQL répliqué et sauvegardé (L3) ; mTLS (L10) ; Keycloak à plusieurs réplicas et console d'administration restreinte (L19) ; stockage persistant, alertes et contrôle d'accès pour Prometheus et Grafana (L20). Voir [architecture-cible.md](../02-architecture/architecture-cible.md) et les limites de [architecture-poc.md](../02-architecture/architecture-poc.md#8-limites-assumées-du-poc).
