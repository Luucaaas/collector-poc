# Collector.shop — POC

Prototype de la plateforme Collector.shop (vente d'objets de collection entre particuliers), réalisé dans le cadre du bloc CESI MAALSI « Superviser et assurer le développement des applications logicielles ».

## Fonctionnalité métier

Un vendeur publie un article ou modifie son prix → contrôle automatique → les acheteurs intéressés sont notifiés et le service anti-fraude reçoit l'événement.

## Stack

| Couche | Technologies |
| --- | --- |
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic, aio-pika |
| Front | React, TypeScript, Vite, MUI |
| Données et messaging | PostgreSQL, RabbitMQ |
| Sécurité | Keycloak (OIDC), TLS via cert-manager, Trivy, ZAP, Gitleaks, Semgrep |
| Plateforme | Docker, Kubernetes local (k3d), Helm, Argo CD |
| CI/CD et qualité | GitHub Actions, GHCR, SonarCloud |
| Observabilité | Prometheus, Grafana |

## Organisation du repo

```
docs/        Processus qualité, architecture, backlog, expérimentations, compétences, sécurité
services/    Services backend FastAPI (catalog, notification, fraud)
frontend/    Application React
tests/       Tests d'acceptation et de charge
deploy/      Cluster local, infrastructure Helm, chart des services, manifests
.github/     Pipelines CI/CD
```

## Démarrage

Instructions à venir (docker-compose puis cluster k3d).
