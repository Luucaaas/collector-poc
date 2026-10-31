# Déploiement

- `local/` : scripts du cluster k3d. `check-tools.sh` vérifie les outils, `deploy.sh` (à venir) crée les Secrets à partir du `.env` puis déploie l'ensemble par `helm upgrade --install`
- `infra/` : values Helm de l'infrastructure (PostgreSQL, RabbitMQ, Keycloak, kube-prometheus-stack allégé) et configuration de Traefik
- `helm/` : chart générique des deux services (réplicas, sondes, HPA, ressources, secrets)
- `k8s/` : manifests complémentaires (Secret TLS du certificat mkcert, Ingress)
