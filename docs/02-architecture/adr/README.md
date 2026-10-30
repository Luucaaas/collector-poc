# Architecture Decision Records

Chaque décision d'architecture structurante fait l'objet d'un ADR au format [MADR](https://adr.github.io/madr/) : contexte et problème, facteurs de décision, options étudiées, décision, conséquences, confirmation. Un ADR accepté n'est pas réécrit : une décision qui change donne lieu à un nouvel ADR qui remplace l'ancien.

Nommage : `NNNN-titre-court.md`.

| N° | Décision | Statut | Date |
| --- | --- | --- | --- |
| [0001](0001-microservices-evenements.md) | Microservices découpés par domaine, communication par événements (outbox, consommateurs idempotents) | Acceptée | 2026-10-30 |
| [0002](0002-fastapi.md) | FastAPI comme framework des services backend | Acceptée | 2026-10-30 |
| [0003](0003-rabbitmq-plutot-que-kafka.md) | RabbitMQ plutôt que Kafka comme broker d'événements | Acceptée | 2026-10-30 |
| [0004](0004-keycloak.md) | Keycloak comme serveur d'identité et d'autorisation | Acceptée | 2026-10-30 |
| [0005](0005-react-typescript.md) | React et TypeScript pour le front | Acceptée | 2026-10-30 |
| [0006](0006-kubernetes-local-k3d-argocd.md) | Kubernetes local (k3d) et déploiement GitOps avec Argo CD, repli sur Oracle OKE | Acceptée sous réserve (critère 5) | 2026-10-30 |
