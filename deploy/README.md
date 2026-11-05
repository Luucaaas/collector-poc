# Déploiement

- `local/` : scripts du cluster k3d. `check-tools.sh` vérifie les outils, `cluster.sh create | verify | delete` crée, contrôle (HTTPS, redirection) et supprime le cluster `collector` (certificat mkcert dans `local/.certs/`, ignoré par Git), `deploy.sh infra` génère les mots de passe manquants dans `local/.env` (ignoré par Git, modèle `.env.example`), crée les Secrets et ConfigMaps puis applique `infra/` et attend que tout soit prêt (relançable), `deploy.sh services <tag>` déploie les deux services par `helm upgrade --install` (voir ci-dessous), `deploy.sh monitoring` installe la pile d'observabilité (voir ci-dessous), `deploy.sh all <tag>` enchaîne `infra`, `monitoring` puis `services` (le tag et les images GHCR sont vérifiés avant tout changement), `check-monitoring.sh` contrôle les cibles Prometheus et les requêtes du tableau de bord, `smoke.sh` contrôle les routes publiques par HTTPS
- `infra/` : manifestes de l'infrastructure, images officielles épinglées par digest : `postgres.yaml` (StatefulSet, rôles créés par `compose/postgres-init/10-roles.sh`), `rabbitmq.yaml` (StatefulSet, Services dont un *headless*, définitions rendues par `compose/render.py`), `keycloak.yaml` (Deployment, Service, Ingress `auth.`, realm rendu sans client de test) ; `monitoring/` : values de kube-prometheus-stack allégé et tableau de bord Grafana (`dashboards/collector-service.json`)
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

## Observabilité : `deploy.sh monitoring`

Installe **kube-prometheus-stack 91.9.0** (chart Helm, release `kps`, namespace `collector`) avec les values allégées de `infra/monitoring/kube-prometheus-stack.yaml` : Prometheus, opérateur, Grafana et kube-state-metrics, sans Alertmanager, node-exporter, règles ni tableaux de bord par défaut (ADR 0008 : seule exception par chart Helm et opérateur). Les six images des composants sont épinglées par `tag@sha256` dans les values (digest de l'index multi-architecture ; changer le tag ET le digest pour monter de version). Le script, dans l'ordre :

1. génère `GRAFANA_ADMIN_PASSWORD` dans `local/.env` s'il manque, puis crée le Secret `grafana-admin` (fichier temporaire 600, `--from-file`, application côté serveur : jamais en argument ni affiché) ;
2. lance `helm upgrade --install kps` : les CRD de Prometheus Operator (dont `ServiceMonitor`) viennent avec le chart ;
3. charge le tableau de bord dans la ConfigMap `collector-dashboards` (label `grafana_dashboard=1`, lu par le sidecar de Grafana) ;
4. ajoute le `ServiceMonitor` des services déjà déployés (`helm upgrade --reuse-values --no-hooks` : pas de migration rejouée, pods inchangés) ;
5. contrôle `https://grafana.127.0.0.1.sslip.io` (200 sur `/api/health`, 401 sans identifiants : accès anonyme désactivé).

Ordre : le CRD `ServiceMonitor` doit exister avant que le chart des services en crée un. `all` installe donc `monitoring` avant `services` ; `services` n'active `serviceMonitor.enabled` que si le CRD existe, et `monitoring` complète les services déjà là (refus, code 1, si la dernière révision Helm d'un service n'est pas `deployed`). Connexion à Grafana : utilisateur `admin`, mot de passe dans `local/.env` (`GRAFANA_ADMIN_PASSWORD`). Prometheus n'est pas exposé : `kubectl -n collector port-forward svc/kps-prometheus 9090`.

Tableau de bord « Collector - service » (variable `service` : catalog-service ou notification-service) : débit, taux de 5xx (seuil de 1 %), latence p95 avec les seuils d'I3 à 300 et 500 ms, réplicas (prêts : kube-state-metrics sur le Deployment ; souhaités : kube-state-metrics sur l'HPA ; cibles `up`), CPU par pod. `local/check-monitoring.sh` vérifie les 4 cibles, envoie du trafic, exécute chaque requête du tableau de bord par l'API de Grafana et relève la mémoire des pods. Stockage de Prometheus non persistant, rétention 2 h (limite L20).

## Modifier le realm Keycloak sur un cluster existant

`--import-realm` n'importe le realm que s'il n'existe pas encore dans la base (stratégie `IGNORE_EXISTING`, visible dans les logs de Keycloak) : modifier `deploy/keycloak/collector-realm.json` n'a aucun effet sur un cluster déjà déployé. Pour appliquer le changement, au choix :

- repartir de zéro : `deploy/local/cluster.sh delete`, `create`, puis `deploy/local/deploy.sh infra` (les mots de passe de `local/.env` sont conservés) ;
- ou ne supprimer que la base de Keycloak : `kubectl -n collector exec postgres-0 -- psql -U postgres -c 'DROP DATABASE keycloak WITH (FORCE)' -c 'CREATE DATABASE keycloak OWNER keycloak' -c 'REVOKE ALL ON DATABASE keycloak FROM PUBLIC'`, relancer `deploy.sh infra` (met à jour le Secret du realm), puis `kubectl -n collector rollout restart deployment/keycloak`.
