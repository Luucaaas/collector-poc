# Déploiement

- `local/` : scripts de création du cluster k3d
- `infra/` : values Helm de l'infrastructure (configuration de Traefik, cert-manager, Keycloak, RabbitMQ, PostgreSQL, monitoring, Argo CD)
- `helm/` : chart des services Collector
- `k8s/` : manifests complémentaires (NetworkPolicies, ClusterIssuer, applications Argo CD)
