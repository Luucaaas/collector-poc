# Déploiement

- `local/` : scripts du cluster k3d. `check-tools.sh` vérifie les outils, `cluster.sh create | verify | delete` crée, contrôle (HTTPS, redirection) et supprime le cluster `collector` (certificat mkcert dans `local/.certs/`, ignoré par Git), `deploy.sh infra` génère les mots de passe manquants dans `local/.env` (ignoré par Git, modèle `.env.example`), crée les Secrets et ConfigMaps puis applique `infra/` et attend que tout soit prêt (relançable), `deploy.sh services <tag>` déploie les deux services par `helm upgrade --install` (voir ci-dessous), `deploy.sh all <tag>` enchaîne `infra` puis `services`, `smoke.sh` contrôle les routes publiques par HTTPS
- `infra/` : manifestes de l'infrastructure, images officielles épinglées par digest : `postgres.yaml` (StatefulSet, rôles créés par `compose/postgres-init/10-roles.sh`), `rabbitmq.yaml` (StatefulSet, Services dont un *headless*, définitions rendues par `compose/render.py`), `keycloak.yaml` (Deployment, Service, Ingress `auth.`, realm rendu sans client de test) ; values de kube-prometheus-stack allégé à venir (P6-04)
- `helm/` : `collector-service/` (chart générique : Deployment à 2 réplicas, sondes, requests et limits, HPA 2 à 5 à 70 % de CPU, Service, Ingress avec Middleware `StripPrefix`, ConfigMap, Job de migration Alembic en hook) et `values/<service>.yaml` (image, Secret, préfixe de route de chaque service)
- `k8s/` : manifests complémentaires (namespace `collector`, réglages de Traefik : certificat par défaut et redirection HTTP vers HTTPS, ressource temporaire de vérification)

## Déployer les services : `deploy.sh services <tag>`

Le tag est celui publié par la CI (`sha-<7 premiers caractères du commit>`, voir les jobs `publish` de GitHub Actions). Exemple : `deploy/local/deploy.sh services sha-bec38ed`.

Le script, dans l'ordre :

1. refuse un tag mal formé, puis vérifie par `docker buildx imagetools inspect` que `ghcr.io/luucaaas/<service>:<tag>` existe : sinon il s'arrête **avant tout changement** ;
2. relève le digest de l'index multi-architecture et le passe au chart : l'image déployée est `tag@sha256:<digest>` ;
3. crée les Secrets `catalog-service-secrets` et `notification-service-secrets` (URL de PostgreSQL et de RabbitMQ, mots de passe pris dans `local/.env`, par fichiers temporaires ; jamais en argument ni affichés) ;
4. lance `helm upgrade --install --wait` pour chaque service : le Job de migration Alembic (hook `pre-install,pre-upgrade`, même image) passe avant les pods ;
5. lance `smoke.sh` ;
6. **en cas d'échec** de l'une de ces étapes : `helm rollback` des services que ce lancement a commencé à mettre à jour, vers leur révision précédente, et code de sortie non nul. Le schéma de la base n'est pas rétabli : une migration doit rester compatible avec la version précédente du service.
   - **Premier déploiement** (aucune révision précédente) : il n'y a rien où revenir ; le script le dit et laisse la release en l'état pour qu'on puisse lire les logs (`kubectl logs`, `helm status`). Il faut alors corriger la cause, puis soit relancer `deploy.sh services <tag>` (Helm reprend la release en échec), soit la supprimer avec `helm -n collector uninstall <service>`.

Il affiche enfin l'`imageID` des pods (digest réellement exécuté) et l'état des Deployments, HPA et pods. Relancer le même tag est sans erreur : nouvelle révision Helm, Job de migration rejoué (sans effet), pods inchangés. Le nombre de réplicas appartient à l'HPA : le chart ne le fixe pas, donc un déploiement pendant une montée en charge ne le ramène pas à 2 (vérifié : 4 réplicas conservés, sans conflit). Le chart exige `image.tag` et `image.digest` : une image sans digest est refusée. La cible CPU de l'HPA reste `<unknown>` environ une minute après le démarrage des pods, le temps que metrics-server ait une mesure.

Le conteneur des services tourne en utilisateur 10001, système de fichiers racine en lecture seule (seul `/tmp` est inscriptible, un `emptyDir`), sans capacité Linux, avec le profil seccomp `RuntimeDefault`. Routage : `https://api.127.0.0.1.sslip.io/catalog/api/v1/...` et `/notification/api/v1/...` ; `/health/*` et `/metrics` ne sont pas routés par l'Ingress.

## Modifier le realm Keycloak sur un cluster existant

`--import-realm` n'importe le realm que s'il n'existe pas encore dans la base (stratégie `IGNORE_EXISTING`, visible dans les logs de Keycloak) : modifier `deploy/keycloak/collector-realm.json` n'a aucun effet sur un cluster déjà déployé. Pour appliquer le changement, au choix :

- repartir de zéro : `deploy/local/cluster.sh delete`, `create`, puis `deploy/local/deploy.sh infra` (les mots de passe de `local/.env` sont conservés) ;
- ou ne supprimer que la base de Keycloak : `kubectl -n collector exec postgres-0 -- psql -U postgres -c 'DROP DATABASE keycloak WITH (FORCE)' -c 'CREATE DATABASE keycloak OWNER keycloak' -c 'REVOKE ALL ON DATABASE keycloak FROM PUBLIC'`, relancer `deploy.sh infra` (met à jour le Secret du realm), puis `kubectl -n collector rollout restart deployment/keycloak`.
