---
statut: acceptée
date: 2026-11-03
décideurs: Lucas (Lead Developer)
---

# 0008 — Infrastructure du POC : images officielles et manifestes simples, sans opérateur

## Contexte et problème

Le POC doit installer sur le cluster k3d trois composants d'infrastructure : **PostgreSQL**, **RabbitMQ** et **Keycloak**, puis l'observabilité (Prometheus, Grafana). Le plus simple et le plus courant, jusqu'en 2025, était d'utiliser les charts Helm de Bitnami. Or **le catalogue Bitnami a changé le 28/08/2025** : les images maintenues ne sont plus publiées gratuitement, et le dépôt `bitnamilegacy` ne reçoit plus de correctifs. Une image sans correctifs de sécurité ferait échouer Trivy, qui bloque le pipeline sur les vulnérabilités CRITICAL et HIGH corrigeables, et irait contre l'exigence de sécurité du contexte.

Le POC tourne sur un Mac de 8 Go, doit se recréer par script (ENF-30) et le Lead Developer découvre Kubernetes : chaque composant ajouté est une compétence de plus à maîtriser et à défendre (ADR 0006 et 0007).

Comment installer l'infrastructure du POC, avec des images maintenues et le moins de composants possible ?

## Facteurs de décision

- **Images maintenues et gratuites**, publiées par l'éditeur du produit.
- **Le moins de composants possible** : chaque outil ajouté doit démontrer un critère de la grille (ADR 0007). Pas de CRD, de webhook ni de certificat interne que l'on ne maîtrise pas.
- **Cohérence avec les ADR existants** : l'ADR 0006 écarte cert-manager pour le POC.
- **Mémoire et disque bornés** : Docker Desktop est limité à environ 8 Go (8 322 555 904 octets, protocoles 1 à 3, §3).
- **Reproductibilité** : tout s'installe par script, sans action manuelle.
- **Défendabilité à l'oral** : ce qu'on déploie, on sait l'expliquer ligne à ligne.

## Options étudiées

1. **Charts Bitnami** (PostgreSQL, RabbitMQ, Keycloak).
2. **Images `bitnamilegacy`** avec les charts existants.
3. **Opérateurs officiels** : RabbitMQ Cluster Operator, CloudNativePG, Keycloak Operator.
4. **Images officielles des éditeurs et manifestes simples** (StatefulSet, Deployment, Services), sans opérateur.

## Décision

**Option 4.** PostgreSQL (`postgres:18.4-alpine`), RabbitMQ (`rabbitmq:4.3.5-management`) et Keycloak (`quay.io/keycloak/keycloak:26.8.0`) sont installés à partir des **images officielles**, par des **manifestes Kubernetes simples** : aucun opérateur, aucune CRD ajoutée, aucun cert-manager. Les versions sont celles des protocoles d'expérimentation.

L'option 3 a d'abord été retenue (journal des décisions du 02/11/2026), **essayée, puis abandonnée** le 03/11/2026 sur décision de Lucas, pour les raisons mesurées suivantes :

- **cert-manager** est exigé par le seul opérateur RabbitMQ (ses webhooks demandent des certificats). L'installer contredit l'ADR 0006, qui le renvoie à la cible.
- **Deux CRD manquaient** au manifeste de Keycloak Operator 26.8.0 : `keycloakoidcclients` et `keycloaksamlclients`. Sans elles, le pod de l'opérateur est en `CrashLoopBackOff` (protocole 2, §6).
- Côté RabbitMQ, **avec l'opérateur, le broker redevenait prêt 54,164 s après la suppression de son pod ; sans opérateur, 9,995 s** (mêmes scénarios, même image, même code : protocole 1, §5). Les republications du producteur passent de 107 à 21.
- **La mémoire baisse de 64 Mi** pour RabbitMQ : 54 Mi (cert-manager) et 19 Mi (opérateur) retirés, le broker passant de 126 à 135 Mi (protocole 1, §5). L'expérimentation consomme 1,5 Go de disque au lieu de 1,8 Go.
- Avec l'opérateur, 2 opérateurs et leurs CRD, webhooks et certificats étaient installés en plus de RabbitMQ ; sans opérateur, aucun objet supplémentaire (protocole 1, §5).
- Côté Keycloak, l'essai avec opérateurs a fait descendre le disque libre à 3,4 Go avant même l'import du realm, la pile avec CloudNativePG consommant plus de 4,5 Go à mi-parcours (cause non décomposée, protocole 2, §6).
- La complexité à défendre baisse : moins de composants, moins d'objets, un comportement lisible dans les manifestes.

La fiabilité est la même : **0 message perdu sur 2 × 1 000** (suppression du consommateur, arrêt propre du broker) et même résultat sur le scénario du message empoisonné, avec ou sans opérateur (protocole 1, §5 et §8).

### Exception : kube-prometheus-stack

**kube-prometheus-stack reste installé par son chart Helm, opérateur Prometheus compris.** C'est une exception assumée à la règle « sans opérateur et sans CRD », et elle s'explique ainsi :

- C'est la façon standard d'obtenir Prometheus, Grafana et les `ServiceMonitor` ; l'écrire à la main, c'est écrire et maintenir la configuration de collecte, le déploiement de Grafana et le chargement des tableaux de bord pour un résultat équivalent.
- Le chart installe bien des CRD (celles de l'opérateur Prometheus, dont `ServiceMonitor`). On ne prétend donc pas que le POC n'a « aucune CRD » : la règle vaut pour les composants **qui gèrent des données métier**.
- Il ne gère pas de données métier : Prometheus et Grafana utilisent des volumes `emptyDir` avec une rétention de 2 h. Perdre cette pile ne fait perdre aucune donnée du produit.
- Il n'exige pas cert-manager : les webhooks d'admission et le TLS de l'opérateur sont désactivés dans les valeurs retenues (protocole 3, §6 et §8).
- **Son coût est mesuré** : environ 600 Mi de mémoire au repos (612 Mi après la charge) et 3,7 Go de disque pendant l'expérimentation (protocole 3, §5 et §8). La pile est allégée : kube-state-metrics et la collecte du kubelet sont gardés pour la démo de montée en charge (réplicas, CPU par pod) ; Alertmanager, node-exporter, supervision du plan de contrôle, règles et tableaux de bord par défaut sont désactivés.
- Son rôle est démontré : les compteurs de Prometheus égalent les requêtes envoyées (écart 0), débit et taux d'erreur s'écartent de 0,1 % des valeurs injectées (protocole 3, §5).

### Conséquences

- ✅ **Images officielles maintenues** : aucun risque lié au catalogue Bitnami, et Trivy peut les analyser sans image « legacy ».
- ✅ **Moins de composants** : ni cert-manager, ni opérateur RabbitMQ, ni CloudNativePG, ni Keycloak Operator, donc ni webhooks ni certificats internes. L'ADR 0006 est respecté.
- ✅ **Plus léger et plus rapide à récupérer** : 64 Mi en moins pour RabbitMQ, retour à l'état prêt en 10 s au lieu de 54 s.
- ✅ **Lisible** : les manifestes de `deploy/infra` se lisent de haut en bas ; chaque ligne se défend à l'oral.
- ✅ **Secrets jamais versionnés** : les scripts `run.sh` des protocoles génèrent déjà les mots de passe (module `secrets` de Python, sauf Grafana, généré par le chart). Pour le POC, `deploy/local/deploy.sh` génère les mots de passe manquants dans un `.env` local non versionné (modèle `.env.example`, versionné, à créer en phase 6), stables d'un déploiement à l'autre, puis crée les Secrets Kubernetes (ADR 0006, S6). Les Secrets Kubernetes sont encodés, non chiffrés (protocole 2, §7).
- ✅ `deploy/infra` contient les **manifestes de PostgreSQL, RabbitMQ et Keycloak** et les **values de kube-prometheus-stack**, au même niveau de versions que les protocoles.
- ❌ **Maintenance manuelle** : sans opérateur, ni sauvegarde, ni bascule, ni mise à jour pilotée d'une base répliquée. Une mise à jour de version est un changement de tag, non testé. Ces services relèvent de la **cible** (opérateurs ou services managés, [architecture-cible.md](../architecture-cible.md)) : limites **L3** (instance PostgreSQL unique) et **L7** (file RabbitMQ sans réplication ni DLQ), détaillées dans [architecture-poc.md](../architecture-poc.md#8-limites-assumées-du-poc).
- ❌ **Durcissement à faire à la main** : aucun `securityContext` n'est posé par un opérateur. Le broker démarre en root (poser un `fsGroup` fait échouer sa recréation, protocole 1, §6) : limites L17 et L18 d'architecture-poc.md.
- ❌ **Une exception à la règle** : kube-prometheus-stack ajoute un opérateur et des CRD. Elle est documentée et mesurée, mais il faut la défendre.
- ❌ **Scan des images d'infrastructure non prévu** : le pipeline (`cicd.md`) analyse par Trivy les images des services du POC, pas `postgres`, `rabbitmq` ni Keycloak. À arbitrer en phase 6.
- ❌ Les valeurs mesurées viennent d'**une exécution de référence par expérimentation**, sur un seul poste (protocoles, §7).

### Confirmation

- Trois protocoles d'expérimentation, rejoués par `run.sh` sur un cluster k3d jetable : [RabbitMQ](../../04-experimentations/01-rabbitmq/protocole.md), [Keycloak, Traefik et TLS](../../04-experimentations/02-keycloak-tls/protocole.md), [observabilité](../../04-experimentations/03-observabilite/protocole.md).
- `git grep -niE "bitnami" -- deploy` ne renvoie rien : aucune image ni aucun chart Bitnami dans le déploiement (à vérifier en phase 6).
- Le déploiement complet de la phase 6 passe sur un cluster neuf en moins de 15 minutes (ENF-30) et tient dans la mémoire de Docker Desktop (budget dans la [synthèse](../../04-experimentations/README.md#synthèse-et-conséquences-pour-le-poc)).
- L'arbitrage sur le scan Trivy des images d'infrastructure est rendu en phase 6 (ou la limite est consignée).
- Le journal des décisions ([02/11/2026 et 03/11/2026](../../suivi/journal-decisions.md)) retrace le choix initial des opérateurs et son remplacement.

## Avantages et inconvénients des options

### Charts Bitnami

- ✅ Un chart par composant, très utilisé, déjà configuré pour la haute disponibilité.
- ❌ Depuis le 28/08/2025, les images maintenues ne sont plus gratuites. Écarté.

### Images `bitnamilegacy`

- ✅ Les charts existants continuent de fonctionner.
- ❌ Aucun correctif : les vulnérabilités connues s'accumulent et Trivy bloquerait la livraison. Choisir un composant non maintenu pour un projet où la sécurité est une exigence de premier plan serait une faute. Écarté.

### Opérateurs officiels

- ✅ Maintenus par les éditeurs, gratuits. Ils gèrent la sauvegarde, la bascule et les mises à jour d'une base ou d'un cluster répliqué.
- ❌ Essayés puis abandonnés pour le POC : cert-manager exigé par l'opérateur RabbitMQ, deux CRD manquantes pour Keycloak Operator, 54 s au lieu de 10 s de retour à l'état prêt, mémoire et disque plus lourds, plus de composants à défendre.
- **Retenus pour la cible**, où le cluster et la base sont répliqués : ce sont les services qu'ils rendent.

### Images officielles et manifestes simples

- ✅ Maintenues, légères, lisibles, rapides à redémarrer ; aucun objet ajouté au cluster.
- ❌ Maintenance, sauvegarde et durcissement à la charge de l'équipe, d'où les limites L3, L7, L17 et L18.
- **Retenue pour le POC.**

> [!TIP]
> **À défendre à l'oral.** Bitnami ne publie plus d'images maintenues gratuitement : on part donc des images officielles des éditeurs. On a d'abord essayé les opérateurs, et on a mesuré. L'opérateur RabbitMQ exige cert-manager, que l'ADR 0006 écarte, et Keycloak Operator demandait deux CRD de plus. Le broker sans opérateur redevient prêt en 10 s au lieu de 54 s, pour 64 Mi de moins, avec la même fiabilité (0 perte sur 2 × 1 000). Les opérateurs servent la sauvegarde, la bascule et les mises à jour d'une base répliquée : c'est la cible, pas un POC à une instance. Seule exception, kube-prometheus-stack : c'est la méthode standard pour Prometheus et Grafana, elle ne gère aucune donnée métier, elle ne demande pas cert-manager, et son coût est mesuré (environ 600 Mi).
