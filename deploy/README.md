# Déploiement

- `local/` : scripts du cluster k3d. `check-tools.sh` vérifie les outils, `cluster.sh create | verify | delete` crée, contrôle (HTTPS, redirection) et supprime le cluster `collector` (certificat mkcert dans `local/.certs/`, ignoré par Git), `deploy.sh` (à venir) crée les Secrets à partir du `.env` puis déploie l'ensemble par `helm upgrade --install`
- `infra/` : manifestes de l'infrastructure (PostgreSQL, RabbitMQ, Keycloak) et values de kube-prometheus-stack allégé (à venir, P6-02 et P6-04)
- `helm/` : chart générique des deux services (réplicas, sondes, HPA, ressources, secrets)
- `k8s/` : manifests complémentaires (namespace `collector`, réglages de Traefik : certificat par défaut et redirection HTTP vers HTTPS, ressource temporaire de vérification)
