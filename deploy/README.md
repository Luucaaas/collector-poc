# Déploiement

- `local/` : scripts du cluster k3d. `check-tools.sh` vérifie les outils, `cluster.sh create | verify | delete` crée, contrôle (HTTPS, redirection) et supprime le cluster `collector` (certificat mkcert dans `local/.certs/`, ignoré par Git), `deploy.sh infra` génère les mots de passe manquants dans `local/.env` (ignoré par Git, modèle `.env.example`), crée les Secrets et ConfigMaps puis applique `infra/` et attend que tout soit prêt (relançable ; les étapes des services viendront en P6-03 par `helm upgrade --install`)
- `infra/` : manifestes de l'infrastructure, images officielles épinglées par digest : `postgres.yaml` (StatefulSet, rôles créés par `compose/postgres-init/10-roles.sh`), `rabbitmq.yaml` (StatefulSet, Services dont un *headless*, définitions rendues par `compose/render.py`), `keycloak.yaml` (Deployment, Service, Ingress `auth.`, realm rendu sans client de test) ; values de kube-prometheus-stack allégé à venir (P6-04)
- `helm/` : chart générique des deux services (réplicas, sondes, HPA, ressources, secrets)
- `k8s/` : manifests complémentaires (namespace `collector`, réglages de Traefik : certificat par défaut et redirection HTTP vers HTTPS, ressource temporaire de vérification)

## Modifier le realm Keycloak sur un cluster existant

`--import-realm` n'importe le realm que s'il n'existe pas encore dans la base (stratégie `IGNORE_EXISTING`, visible dans les logs de Keycloak) : modifier `deploy/keycloak/collector-realm.json` n'a aucun effet sur un cluster déjà déployé. Pour appliquer le changement, au choix :

- repartir de zéro : `deploy/local/cluster.sh delete`, `create`, puis `deploy/local/deploy.sh infra` (les mots de passe de `local/.env` sont conservés) ;
- ou ne supprimer que la base de Keycloak : `kubectl -n collector exec postgres-0 -- psql -U postgres -c 'DROP DATABASE keycloak WITH (FORCE)' -c 'CREATE DATABASE keycloak OWNER keycloak' -c 'REVOKE ALL ON DATABASE keycloak FROM PUBLIC'`, relancer `deploy.sh infra` (met à jour le Secret du realm), puis `kubectl -n collector rollout restart deployment/keycloak`.
