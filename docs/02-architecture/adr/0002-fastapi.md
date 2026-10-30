---
statut: acceptée
date: 2026-10-30
décideurs: Lucas (Lead Developer)
---

# 0002 — FastAPI comme framework des services backend

## Contexte et problème

Les trois services du POC exposent des API REST sécurisées par JWT, valident strictement leurs entrées, accèdent à PostgreSQL et publient ou consomment des messages RabbitMQ. L'équipe maîtrise surtout Python. Le POC doit être livré vite, avec une couverture de tests élevée (ENF-22) et un contrat d'API publié (ENF-27).

Quel framework retenir pour les services backend ?

## Facteurs de décision

- Compétences de l'équipe, principalement en Python.
- Support natif de l'asynchrone : un même processus sert les requêtes HTTP et consomme des messages AMQP (aio-pika).
- Validation stricte des entrées et génération automatique du contrat OpenAPI (ENF-07, ENF-27).
- Légèreté adaptée à des microservices : démarrage rapide, image réduite, peu de mémoire par réplica.
- Testabilité : injection de dépendances, client de test, surcharge simple de l'authentification dans les tests.

## Options étudiées

1. **FastAPI** (Python, ASGI) avec Pydantic v2 et SQLAlchemy 2.0.
2. **Django + Django REST Framework** (Python).
3. **Flask** (Python, WSGI).
4. **Spring Boot** (Java).
5. **NestJS** (TypeScript, Node.js).

## Décision

**Option 1 : FastAPI**, avec Pydantic v2 pour la validation, SQLAlchemy 2.0 en mode asynchrone pour l'accès aux données, Alembic pour les migrations, PyJWT pour la vérification des jetons, aio-pika pour RabbitMQ, structlog pour les logs JSON et prometheus-fastapi-instrumentator pour les métriques. Les dépendances sont gérées par uv.

### Conséquences

- ✅ Les schémas Pydantic servent à la fois de validation, de documentation OpenAPI et de typage : une seule source de vérité pour le contrat.
- ✅ L'asynchrone natif (ASGI, `async`/`await`) permet de consommer RabbitMQ dans le même processus que l'API, sans thread supplémentaire.
- ✅ Le système de dépendances (`Depends`) rend l'authentification et l'accès à la base injectables, donc remplaçables dans les tests.
- ✅ L'équipe est productive tout de suite : courbe d'apprentissage faible pour des développeurs Python.
- ❌ FastAPI est un micro-framework : authentification, migrations, configuration et structure du projet sont à assembler soi-même. Atténuation : un gabarit de service commun aux trois services.
- ❌ L'asynchrone exige de la discipline : un appel bloquant dans une coroutine bloque toute la boucle d'événements. Atténuation : uniquement des pilotes asynchrones (asyncpg, aio-pika) et une revue de code dédiée.
- ❌ Python est moins performant en calcul pur que Java ou Go. Cela reste sans effet ici, car les services sont limités par les entrées-sorties (base, broker) et non par le CPU.

### Confirmation

Le test de charge Locust valide les cibles de temps de réponse d'ENF-12 (p95 < 300 ms en lecture, < 500 ms en publication, à 50 utilisateurs). La couverture mesurée par pytest-cov valide ENF-22.

## Avantages et inconvénients des options

### Django + Django REST Framework

- ✅ Très complet : ORM, migrations, back-office d'administration, authentification.
- ❌ Monolithique et conçu pour une base unique, il apporte beaucoup de fonctions inutiles à un microservice.
- ❌ Asynchrone partiel : l'ORM reste majoritairement synchrone, ce qui complique la consommation AMQP dans le même processus.

### Flask

- ✅ Simple et léger.
- ❌ Synchrone (WSGI). Ni validation ni OpenAPI natives : il faut ajouter des extensions.

### Spring Boot

- ✅ Très mature, riche en intégrations (Spring Security, Spring AMQP), performant.
- ❌ Hors des compétences de l'équipe : montée en compétences longue, incompatible avec le calendrier du POC.
- ❌ Empreinte mémoire plus élevée par réplica, sensible sur un cluster local.

### NestJS

- ✅ TypeScript partagé avec le front, architecture modulaire.
- ❌ Ajoute un second écosystème de backend à maîtriser pour une équipe Python.

## Plus d'informations

- Le choix du framework n'est pas une expérimentation au sens de la consigne, qui exclut « l'implémentation d'un composant avec un framework ». Les protocoles portent sur les plateformes : broker, Keycloak, Kubernetes, CI/CD.

> [!TIP]
> **À défendre à l'oral.** FastAPI n'est pas choisi parce qu'il est « à la mode » : son modèle asynchrone permet de servir HTTP et de consommer AMQP dans le même processus, et Pydantic fait du contrat d'API une source unique de validation, de typage et de documentation. Le risque connu, bloquer la boucle d'événements avec un appel synchrone, est maîtrisé par le choix de pilotes asynchrones.
