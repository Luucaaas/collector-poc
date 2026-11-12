---
statut: acceptée (mise à jour le 2026-10-31, voir ADR 0007)
date: 2026-10-30
décideurs: Lucas (Lead Developer)
---

# 0001 — Microservices découpés par domaine, communication par événements

## Contexte et problème

Collector.shop doit « faciliter la mise à jour des fonctionnalités ou l'ajout rapide de nouvelles fonctionnalités » : enchères, ventes en direct, bot d'avant-vente, analyse des ventes (EF-35). Un même fait métier, comme la publication d'un article ou un changement de prix, intéresse plusieurs fonctions : notifications aux acheteurs, détection de fraude, puis recherche, recommandations et publicité. La direction n'a pas encore décidé si l'outil anti-fraude sera développé ou acheté (EF-25). L'équipe compte aujourd'hui trois développeurs et va grandir.

Comment structurer l'application pour ajouter des fonctionnalités sans modifier l'existant, tout en gardant une complexité supportable ?

## Facteurs de décision

- Ajouter un consommateur d'un fait métier sans modifier son producteur (EF-35, ENF-28).
- Pouvoir remplacer le composant anti-fraude par un produit acheté (EF-25).
- Isoler les pannes : une panne de la détection de fraude ne doit pas empêcher un vendeur de publier (ENF-16).
- Faire évoluer et déployer chaque domaine indépendamment, à mesure que l'équipe grandit.
- Garder une charge d'exploitation compatible avec une petite équipe et un POC sur un poste de développement.

## Options étudiées

1. **Monolithe modulaire** : une application, une base, des modules par domaine.
2. **Microservices en appels REST synchrones** : le catalogue appelle la notification et la fraude à chaque publication.
3. **Microservices orientés événements** : chaque service possède sa base. Le catalogue publie des événements sur un broker, et les autres services s'y abonnent.

## Décision

**Option 3 : microservices orientés événements**, avec les règles suivantes :

- une base de données par service, sans base partagée (ENF-21) ;
- REST synchrone uniquement entre le client et un service ; un service ne dépend jamais d'un appel synchrone vers un autre service pour terminer une écriture ;
- événements publiés sur un exchange `topic`, livrés « au moins une fois » ;
- événements porteurs de l'état utile (*event-carried state transfer*), pour que les consommateurs n'aient pas à rappeler le producteur ;
- contrats d'événements versionnés (`schema_version`), avec un `event_id` qui sert de clé d'idempotence.

**Mise en œuvre dans le POC** (ADR [0007](0007-simplification-perimetre-poc.md)) :

- deux services : `catalog-service` produit les événements, `notification-service` les consomme ;
- une instance PostgreSQL, avec une base logique et un utilisateur par service ;
- publication de l'événement **juste après le commit** de la transaction, sans outbox ;
- l'outil anti-fraude n'est pas implémenté. Il reste un **point d'extension** : il s'abonnera à l'exchange `article.events` avec sa propre file, sans modification de `catalog-service`.

**Dans la cible** : une instance de base par service, publication par **transactional outbox**, **consommateurs idempotents** par une table `processed_events`, *dead-letter queues* (ENF-18, ENF-19).

### Conséquences

- ✅ Ajouter un consommateur se réduit à créer une file et une liaison. Le POC le montre en liant une file supplémentaire à l'exchange pendant la démo : elle reçoit les événements sans que `catalog-service` soit modifié.
- ✅ Le catalogue reste disponible quand `notification-service` est en panne : les messages s'accumulent dans la file durable et sont traités à son retour.
- ✅ L'outil anti-fraude pourra être interne ou acheté : il ne dépendra que du contrat d'événements.
- ❌ **Cohérence à terme** (*eventual consistency*) : une notification arrive quelques dizaines de millisecondes après la publication. C'est acceptable pour ce besoin, avec une cible de p95 inférieur à 2 s (ENF-14).
- ❌ **Fenêtre de perte dans le POC** : sans outbox, un événement est perdu si le broker est indisponible entre le commit et la publication. La cible la ferme avec l'outbox.
- ❌ **Complexité opérationnelle** : broker à exploiter, plusieurs bases, traçage d'un parcours sur plusieurs services. Atténuation : identifiant de corrélation propagé dans les logs et les événements, métriques par service, déploiement automatisé par Helm.
- ❌ Tests plus coûteux : il faut des tests d'intégration avec un vrai broker (testcontainers) et des tests de contrat sur les événements.

### Confirmation

- Les tests d'acceptation de US-05 montrent qu'une publication déclenche la notification des acheteurs intéressés, en moins de 2 s.
- La contrainte d'unicité `(user_id, source_event_id)` garantit qu'un message relivré ne produit pas de seconde notification.
- L'utilisateur PostgreSQL de `notification-service` ne peut pas se connecter à `catalog_db` : l'isolation des données est vérifiée.
- Une file supplémentaire liée à `article.events` reçoit les événements sans modification ni redéploiement du catalogue : prouvé par le test d'intégration `services/catalog-service/tests/test_rabbitmq.py` (une démonstration en soutenance était envisagée, elle n'a pas été retenue dans la démo de 6 minutes).

## Avantages et inconvénients des options

### Monolithe modulaire

- ✅ Le plus simple à développer, tester et déployer. Transactions ACID entre modules.
- ✅ Adapté à une équipe de trois personnes au démarrage.
- ❌ Un seul déploiement : chaque évolution redéploie tout, et une fuite mémoire dans un module affecte toute l'application.
- ❌ La montée en charge se fait en bloc, même si un seul domaine est sollicité.
- ❌ Remplacer l'anti-fraude par un produit acheté demande quand même de construire une intégration asynchrone.
- ❌ Ne permet pas de démontrer la communication interservice ni l'orchestration attendues par l'évaluation.

### Microservices en appels REST synchrones

- ✅ Modèle simple à comprendre et à déboguer.
- ❌ **Couplage temporel** : si `fraud-service` est lent ou en panne, la publication échoue ou ralentit.
- ❌ Le catalogue doit connaître et appeler chaque nouveau consommateur : chaque fonctionnalité ajoutée le modifie.
- ❌ La disponibilité globale est le produit des disponibilités des services appelés.

### Microservices orientés événements

- ✅ Couplage faible, dans le temps comme dans le code. Extension par ajout de consommateurs.
- ❌ Cohérence à terme, broker à exploiter, débogage distribué (voir les conséquences).

## Plus d'informations

- Une transaction distribuée (2PC) entre la base et le broker a été écartée : RabbitMQ ne la supporte pas, et elle bloquerait la base en cas d'indisponibilité du broker. L'outbox de la cible apporte la même garantie avec une transaction locale.
- Le choix du broker fait l'objet de l'ADR [0003](0003-rabbitmq-plutot-que-kafka.md).
- Contrats : [contrats.md](../contrats.md). Vues : [architecture-cible.md](../architecture-cible.md), [architecture-poc.md](../architecture-poc.md).

> [!TIP]
> **À défendre à l'oral.** On n'a pas découpé en microservices « par principe » : le besoin explicite d'ajouter des fonctionnalités qui réagissent aux mêmes faits métier, et de pouvoir acheter l'anti-fraude, justifie le découplage par événements. On assume le prix à payer (cohérence à terme, exploitation). Le POC le réduit au minimum, deux services et une publication directe, et la cible le maîtrise par l'outbox, l'idempotence et l'observabilité.
