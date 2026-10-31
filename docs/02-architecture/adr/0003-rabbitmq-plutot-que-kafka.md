---
statut: acceptée (mise à jour le 2026-10-31, voir ADR 0007)
date: 2026-10-30
décideurs: Lucas (Lead Developer)
---

# 0003 — RabbitMQ plutôt que Kafka comme broker d'événements

## Contexte et problème

L'ADR [0001](0001-microservices-evenements.md) retient une communication par événements. Il faut un broker qui distribue chaque événement du catalogue à plusieurs consommateurs, garantisse qu'aucun événement n'est perdu (ENF-18), isole les messages en échec et tourne sur un cluster Kubernetes local aux ressources limitées.

Le volume attendu en V1 est modeste. **Hypothèse de dimensionnement**, à confirmer par la direction : quelques milliers d'articles publiés et de changements de prix par jour, soit quelques événements par seconde au pic. C'est un ordre de grandeur cohérent avec une start-up qui lance sa place de marché, pas une mesure.

Quel broker retenir ?

## Facteurs de décision

- Distribution d'un même événement à plusieurs consommateurs (*publish/subscribe*), avec un routage fin par type d'événement.
- Fiabilité : persistance, acquittement par message, file des messages en échec (*dead-letter queue*), relivraison bornée.
- Empreinte mémoire et simplicité d'exploitation, sur un poste de développement comme pour une petite équipe.
- Adéquation au volume de la V1, sans surdimensionnement.
- Maturité de la bibliothèque Python asynchrone.

## Options étudiées

1. **RabbitMQ** : broker AMQP 0-9-1, exchanges et files.
2. **Apache Kafka** : journal distribué partitionné (mode KRaft, sans ZooKeeper).
3. **NATS JetStream** : messagerie légère avec persistance.
4. **Redis Streams**.

## Décision

**Option 1 : RabbitMQ**, avec un exchange `topic` durable (`article.events`), une file durable par consommateur, des messages persistants, les *publisher confirms* côté producteur et un acquittement manuel côté consommateur. Le client Python est aio-pika.

- **Dans le POC** (ADR 0007) : un seul nœud RabbitMQ et une seule file classique, `notification.article-events`.
- **Dans la cible** : cluster de 3 nœuds, *quorum queues*, et *dead-letter queue* propre à chaque consommateur après 5 tentatives (`x-delivery-limit`, clé de routage de dead-letter par file, stratégie `at-least-once`).

### Conséquences

- ✅ Le modèle exchange → files correspond exactement au besoin : chaque service reçoit sa copie, et un nouveau consommateur se branche par une simple liaison.
- ✅ Acquittement par message, et *dead-letter queues* natives pour la cible : un message qui échoue n'en bloque pas d'autres et reste analysable.
- ✅ Empreinte réduite : une instance tient dans quelques centaines de Mo de mémoire. L'interface de gestion et les métriques Prometheus sont intégrées.
- ✅ Les *quorum queues* (réplication Raft) offrent la haute disponibilité de la cible avec un cluster de 3 nœuds, sans changer le code.
- ❌ Pas de rétention longue ni de relecture de l'historique par défaut : un message acquitté disparaît. Un futur service, comme l'analyse des ventes, ne pourra pas relire les événements passés. Atténuation : les RabbitMQ Streams, ou l'ajout de Kafka pour la plateforme de données si le besoin se confirme.
- ❌ Débit maximal inférieur à celui de Kafka, sans incidence au volume de la V1.
- ❌ Ordre garanti seulement au sein d'une file et avec un seul consommateur actif. Le contrat d'événements en tient compte : les consommateurs ignorent un `price_changed` plus ancien que le dernier traité.

### Confirmation

Un protocole d'expérimentation (`docs/04-experimentations`) déploie RabbitMQ dans le cluster k3d, mesure la publication et la consommation, puis vérifie trois comportements : la perte d'un consommateur (les messages s'accumulent puis sont consommés à son retour), le redémarrage du broker (aucun message persistant n'est perdu) et l'ajout d'une file liée à l'exchange, qui reçoit les événements sans modification du producteur.

## Avantages et inconvénients des options

### Apache Kafka

- ✅ Débit très élevé, rétention configurable et relecture de l'historique (*replay*), adapté à l'*event sourcing* et à l'analytique.
- ❌ **Surdimensionné pour la V1** : partitions, groupes de consommateurs, réglage de la rétention et des réplicas, pour quelques événements par seconde.
- ❌ Empreinte mémoire nettement plus forte (JVM), problématique sur un cluster local de 8 Go.
- ❌ Pas de *dead-letter queue* native : il faut la construire avec des topics de relivraison.
- ❌ Courbe d'apprentissage plus forte pour l'équipe.

### NATS JetStream

- ✅ Très léger et performant, persistance et relecture disponibles.
- ❌ Client Python asynchrone moins utilisé que aio-pika, et pas d'équivalent direct des exchanges `topic` et des *dead-letter queues* : la gestion des échecs se construit avec les limites de relivraison et des sujets dédiés.

### Redis Streams

- ✅ Simple si Redis est déjà présent.
- ❌ Persistance et durabilité moins fortes. Routage pauvre : pas d'équivalent des exchanges `topic`.

## Plus d'informations

- Le choix est réversible à coût maîtrisé : le code métier ne voit qu'une interface `EventPublisher` et des consommateurs. Le contrat d'événements (JSON, `event_id`, `schema_version`) ne dépend pas du broker.
- Kafka reste envisagé dans l'architecture cible pour la plateforme de données (analyse des ventes, recommandations sur le parcours), si la rétention et la relecture deviennent nécessaires.

> [!TIP]
> **À défendre à l'oral.** Kafka est un journal distribué conçu pour des volumes massifs et la relecture de l'historique. RabbitMQ est un broker de messages qui route et acquitte message par message. Notre besoin en V1 est de distribuer de façon fiable quelques événements par seconde à plusieurs consommateurs, avec gestion des échecs : c'est exactement le modèle de RabbitMQ. On sait nommer ce qu'on perd (la relecture) et comment le récupérer (Streams, ou Kafka plus tard pour la donnée).
