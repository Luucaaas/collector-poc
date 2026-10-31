# Architecture Decision Records

Chaque décision d'architecture structurante fait l'objet d'un ADR au format [MADR](https://adr.github.io/madr/) : contexte et problème, facteurs de décision, options étudiées, décision, conséquences, confirmation. Une décision qui change est soit mise à jour avec une mention dans son en-tête et un renvoi à l'ADR qui motive le changement, soit remplacée par un nouvel ADR.

Nommage : `NNNN-titre-court.md`.

| N° | Décision | Statut | Date |
| --- | --- | --- | --- |
| [0001](0001-microservices-evenements.md) | Microservices découpés par domaine, communication par événements. POC : 2 services, publication juste après le commit. Cible : outbox, consommateurs idempotents | Acceptée, mise à jour par 0007 | 2026-10-30, 2026-10-31 |
| [0002](0002-fastapi.md) | FastAPI comme framework des services backend | Acceptée | 2026-10-30 |
| [0003](0003-rabbitmq-plutot-que-kafka.md) | RabbitMQ plutôt que Kafka comme broker d'événements | Acceptée, mise à jour par 0007 | 2026-10-30, 2026-10-31 |
| [0004](0004-keycloak.md) | Keycloak comme serveur d'identité et d'autorisation | Acceptée | 2026-10-30 |
| [0005](0005-react-typescript.md) | React et TypeScript pour le front | Acceptée, mise à jour par 0007 | 2026-10-30, 2026-10-31 |
| [0006](0006-kubernetes-local-k3d-argocd.md) | Kubernetes local (k3d), Traefik, Helm et déploiement par script. Argo CD et cert-manager dans la cible, repli sur Oracle OKE | Acceptée sous réserve (critère 5), mise à jour par 0007 | 2026-10-30, 2026-10-31 |
| [0007](0007-simplification-perimetre-poc.md) | Simplification du périmètre du POC : chaque retrait justifié, avec son risque | Acceptée | 2026-10-31 |
