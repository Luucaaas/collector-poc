---
statut: acceptée
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
- événements publiés via le patron **transactional outbox**, livrés « au moins une fois », traités par des **consommateurs idempotents** (ENF-18, ENF-19) ;
- événements porteurs de l'état utile (*event-carried state transfer*), pour que les consommateurs n'aient pas à rappeler le producteur ;
- contrats d'événements versionnés (`schema_version`).

Le POC limite le découpage à trois services, `catalog`, `notification` et `fraud`, suffisants pour démontrer le principe sur la fonctionnalité métier retenue.

### Conséquences

- ✅ Ajouter un consommateur se réduit à créer une file et une liaison : le POC le montre avec deux consommateurs indépendants des mêmes événements.
- ✅ Le catalogue reste disponible quand la notification, la fraude ou même le broker sont en panne : l'outbox conserve les événements en attente.
- ✅ L'outil anti-fraude peut être remplacé : il ne dépend que du contrat d'événements.
- ❌ **Cohérence à terme** (*eventual consistency*) : une notification arrive quelques centaines de millisecondes après la publication. C'est acceptable pour ce besoin, avec une cible de p95 inférieur à 2 s (ENF-14).
- ❌ **Complexité opérationnelle** : broker à exploiter, plusieurs bases, traçage d'un parcours sur plusieurs services. Atténuation : identifiant de corrélation propagé dans les logs et les événements, métriques par service, déploiement automatisé par Helm et Argo CD.
- ❌ Tests plus coûteux : il faut des tests d'intégration avec un vrai broker (testcontainers) et des tests de contrat sur les événements.

### Confirmation

- Le test d'intégration « broker arrêté pendant une publication » montre que l'événement est livré au redémarrage.
- Le test d'idempotence montre qu'un événement livré deux fois ne produit qu'une notification.
- La NetworkPolicy refuse la connexion de `fraud-service` à `catalog_db` : l'isolation des données est vérifiée.

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

- Une transaction distribuée (2PC) entre la base et le broker a été écartée : RabbitMQ ne la supporte pas, et elle bloquerait la base en cas d'indisponibilité du broker. L'outbox apporte la même garantie avec une transaction locale.
- Le choix du broker fait l'objet de l'ADR [0003](0003-rabbitmq-plutot-que-kafka.md).
- Contrats : [contrats.md](../contrats.md). Vues : [architecture-cible.md](../architecture-cible.md), [architecture-poc.md](../architecture-poc.md).

> [!TIP]
> **À défendre à l'oral.** On n'a pas découpé en microservices « par principe » : le besoin explicite d'ajouter des fonctionnalités qui réagissent aux mêmes faits métier, et de pouvoir acheter l'anti-fraude, justifie le découplage par événements. On assume le prix à payer (cohérence à terme, exploitation) et on le maîtrise par l'outbox, l'idempotence et l'observabilité.
