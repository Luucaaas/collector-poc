# Collector.shop — POC

Prototype de la plateforme Collector.shop (vente d'objets de collection entre particuliers), réalisé dans le cadre du bloc CESI MAALSI « Superviser et assurer le développement des applications logicielles ».

## Fonctionnalité métier

Un vendeur publie un article ou modifie son prix → contrôle automatique → un événement est publié sur RabbitMQ → les acheteurs intéressés sont notifiés. Un outil anti-fraude pourra s'abonner aux mêmes événements sans modifier le catalogue.

## Stack

| Couche | Technologies |
| --- | --- |
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic, aio-pika |
| Front | React, TypeScript, Vite, MUI |
| Données et messaging | PostgreSQL, RabbitMQ |
| Sécurité | Keycloak (OIDC + PKCE), TLS par Traefik (certificat mkcert), SonarCloud, Trivy |
| Plateforme | Docker, Kubernetes local (k3d), Traefik, Helm (déploiement par script) |
| CI/CD et qualité | GitHub Actions, GHCR, SonarCloud |
| Observabilité | Prometheus, Grafana |

## Organisation du repo

```
docs/        Processus qualité, architecture, backlog, expérimentations, compétences, sécurité
services/    Services backend FastAPI (catalog, notification)
frontend/    Application React
tests/       Tests d'acceptation et de charge
deploy/      Cluster local, infrastructure Helm, chart générique des services, script de déploiement
.github/     Pipelines CI/CD
```

## Démarrage

Instructions à venir (cluster k3d, puis `deploy/local/deploy.sh`).
