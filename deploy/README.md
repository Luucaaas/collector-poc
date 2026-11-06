# Déploiement

- `local/` : scripts du cluster k3d. `check-tools.sh` vérifie les outils, `cluster.sh create | verify | delete` crée, contrôle (HTTPS, redirection) et supprime le cluster `collector` (`create` exige 10 000 Mo libres dans la VM Docker et les ports 80 et 443 libres) (certificat mkcert dans `local/.certs/`, ignoré par Git), `deploy.sh infra` génère les mots de passe manquants dans `local/.env` (ignoré par Git, modèle `.env.example`), crée les Secrets et ConfigMaps puis applique `infra/` et attend que tout soit prêt (relançable), `deploy.sh services <tag>` déploie les deux services et le front par `helm upgrade --install` (voir ci-dessous), `deploy.sh realm` applique un realm Keycloak modifié à un cluster existant (voir ci-dessous), `deploy.sh monitoring` installe la pile d'observabilité (voir ci-dessous), `deploy.sh all <tag>` enchaîne `infra`, `monitoring` puis `services` (le tag et les images GHCR sont vérifiés avant tout changement), `check-monitoring.sh` contrôle les cibles Prometheus et les requêtes du tableau de bord, `smoke.sh` contrôle les routes publiques par HTTPS, `publish-test-event.sh` publie un `article.published` de test sur RabbitMQ avec le compte `catalog` et vérifie que `notification-service` le consomme (voir ci-dessous)
- `infra/` : manifestes de l'infrastructure, images officielles épinglées par digest : `postgres.yaml` (StatefulSet, rôles créés par `compose/postgres-init/10-roles.sh`), `rabbitmq.yaml` (StatefulSet, Services dont un *headless*, définitions rendues par `compose/render.py`), `keycloak.yaml` (Deployment, Service, Ingress `auth.`, realm rendu sans client de test) ; `monitoring/` : values de kube-prometheus-stack allégé et tableau de bord Grafana (`dashboards/collector-service.json`)
- `helm/` : `collector-service/` (chart générique : Deployment à 2 réplicas, sondes, requests et limits, HPA 2 à 5 à 70 % de CPU, Service, Ingress avec Middleware `StripPrefix`, ConfigMap, Job de migration Alembic en hook) et `values/<service>.yaml` (image, Secret, préfixe de route de chaque service)
- `k8s/` : manifests complémentaires (namespace `collector`, réglages de Traefik : certificat par défaut et redirection HTTP vers HTTPS, ressource temporaire de vérification)

## Déployer les services et le front : `deploy.sh services <tag>`

Le tag est celui publié par la CI (`sha-<7 premiers caractères du commit>`, voir les jobs `publish` de GitHub Actions). Exemple : `deploy/local/deploy.sh services sha-bec38ed`.

Le script, dans l'ordre :

1. refuse un tag mal formé, puis vérifie par `docker buildx imagetools inspect` que `ghcr.io/luucaaas/<composant>:<tag>` (`catalog-service`, `notification-service`, `frontend`) existe : sinon il s'arrête **avant tout changement** ;
2. relève le digest de l'index multi-architecture et le passe au chart : l'image déployée est `tag@sha256:<digest>` ;
3. crée les Secrets `catalog-service-secrets` et `notification-service-secrets` (URL de PostgreSQL et de RabbitMQ, mots de passe pris dans `local/.env`, par fichiers temporaires ; jamais en argument ni affichés) ;
4. lance `helm upgrade --install --wait` pour chaque composant, le front en dernier : le Job de migration Alembic (hook `pre-install,pre-upgrade`, même image) passe avant les pods ;
5. lance `smoke.sh` ;
6. **en cas d'échec** de l'une de ces étapes : `helm rollback` des composants que ce lancement a commencé à mettre à jour, vers leur révision précédente, et code de sortie non nul. Le schéma de la base n'est pas rétabli : une migration doit rester compatible avec la version précédente du service.
   - **Premier déploiement** (aucune révision précédente) : il n'y a rien où revenir ; le script le dit et laisse la release en l'état pour qu'on puisse lire les logs (`kubectl logs`, `helm status`). Il faut alors corriger la cause, puis soit relancer `deploy.sh services <tag>` (Helm reprend la release en échec), soit la supprimer avec `helm -n collector uninstall <service>`.

Il affiche enfin l'`imageID` des pods (digest réellement exécuté) et l'état des Deployments, HPA et pods. Relancer le même tag est sans erreur : nouvelle révision Helm, Job de migration rejoué (sans effet), pods inchangés. Le nombre de réplicas appartient à l'HPA : le chart ne le fixe pas, donc un déploiement pendant une montée en charge ne le ramène pas à 2 (vérifié : 4 réplicas conservés, sans conflit). Le chart exige `image.tag` et `image.digest` : une image sans digest est refusée. La cible CPU de l'HPA reste `<unknown>` environ une minute après le démarrage des pods, le temps que metrics-server ait une mesure.

Le conteneur des services tourne en utilisateur 10001, système de fichiers racine en lecture seule (seul `/tmp` est inscriptible, un `emptyDir`), sans capacité Linux, avec le profil seccomp `RuntimeDefault`. Routage : `https://api.127.0.0.1.sslip.io/catalog/api/v1/...` et `/notification/api/v1/...` ; `/health/*` et `/metrics` ne sont pas routés par l'Ingress.

## Retour arrière démontré et événement de test

- **Déployer une version défaillante pour démontrer le retour arrière** (le fichier s'applique aux trois composants ; pour ne viser que le front, une variable que lui seul lit, par exemple `config.CSP_CONNECT_SRC` avec un guillemet qui casse la configuration nginx : le pod ne devient jamais prêt) : `DEPLOY_VALUES=<fichier de values Helm> deploy/local/deploy.sh services <tag>` ajoute ce fichier après les values du service (`-f`). Exemple utilisé au protocole : `resources.limits.memory: 24Mi`, les pods sont tués par manque de mémoire (OOMKilled) avant d'être prêts, `helm --wait` échoue au bout de 5 min, `deploy.sh` annule par `helm rollback` et sort en code 1. Pendant ce temps le `RollingUpdate` (`maxUnavailable: 0`) garde les anciens pods en service. Mesures : [protocole 4](../docs/04-experimentations/04-deploiement/protocole.md). **Le retour arrière ne défait pas les migrations Alembic** (limite L23).
- **`publish-test-event.sh`** : le mot de passe du compte RabbitMQ `catalog` (droits : configure et write sur l'exchange `article.events` seulement, read vide, aucune étiquette d'administration) est lu dans `local/.env` et transmis par l'entrée standard de `kubectl exec` à un petit programme Python lancé dans un pod de `catalog-service` (aio-pika y est installé ; le compte n'a pas accès à l'API HTTP de RabbitMQ) : jamais en argument ni affiché (une erreur de connexion n'affiche que le type de l'exception, jamais la chaîne AMQP : vérifié avec un faux mot de passe). Le script lit `events_consumed_total{outcome="processed"}` dans chaque pod de `notification-service`, publie, puis vérifie que la somme a augmenté. La catégorie de l'événement n'existe pas : aucun acheteur n'est notifié, l'événement est quand même consommé.

## Observabilité : `deploy.sh monitoring`

Installe **kube-prometheus-stack 91.9.0** (chart Helm, release `kps`, namespace `collector`) avec les values allégées de `infra/monitoring/kube-prometheus-stack.yaml` : Prometheus, opérateur, Grafana et kube-state-metrics, sans Alertmanager, node-exporter, règles ni tableaux de bord par défaut (ADR 0008 : seule exception par chart Helm et opérateur). Les six images des composants sont épinglées par `tag@sha256` dans les values (digest de l'index multi-architecture ; changer le tag ET le digest pour monter de version). Le script, dans l'ordre :

1. génère `GRAFANA_ADMIN_PASSWORD` dans `local/.env` s'il manque, puis crée le Secret `grafana-admin` (fichier temporaire 600, `--from-file`, application côté serveur : jamais en argument ni affiché) ;
2. lance `helm upgrade --install kps` : les CRD de Prometheus Operator (dont `ServiceMonitor`) viennent avec le chart ;
3. charge le tableau de bord dans la ConfigMap `collector-dashboards` (label `grafana_dashboard=1`, lu par le sidecar de Grafana) ;
4. ajoute le `ServiceMonitor` des services déjà déployés (`helm upgrade --reuse-values --no-hooks` : pas de migration rejouée, pods inchangés) ;
5. contrôle `https://grafana.127.0.0.1.sslip.io` (200 sur `/api/health`, 401 sans identifiants : accès anonyme désactivé).

Ordre : le CRD `ServiceMonitor` doit exister avant que le chart des services en crée un. `all` installe donc `monitoring` avant `services` ; `services` n'active `serviceMonitor.enabled` que si le CRD existe, et `monitoring` complète les services déjà là (refus, code 1, si la dernière révision Helm d'un service n'est pas `deployed`). Connexion à Grafana : utilisateur `admin`, mot de passe dans `local/.env` (`GRAFANA_ADMIN_PASSWORD`). Prometheus n'est pas exposé : `kubectl -n collector port-forward svc/kps-prometheus 9090`.

Tableau de bord « Collector - service » (variable `service` : catalog-service ou notification-service) : débit, taux de 5xx (seuil de 1 %), latence p95 avec les seuils d'I3 à 300 et 500 ms, réplicas (prêts : kube-state-metrics sur le Deployment ; souhaités : kube-state-metrics sur l'HPA ; cibles `up`), CPU par pod. `local/check-monitoring.sh` vérifie les 4 cibles, envoie du trafic, exécute chaque requête du tableau de bord par l'API de Grafana et relève la mémoire des pods. Stockage de Prometheus non persistant, rétention 2 h (limite L20).

## Modifier le realm Keycloak sur un cluster existant : `deploy.sh realm`

`--import-realm` n'importe le realm que s'il n'existe pas encore dans la base (stratégie `IGNORE_EXISTING`, visible dans les logs de Keycloak) : modifier `deploy/keycloak/collector-realm.json` n'a aucun effet sur un cluster déjà déployé. La documentation officielle de Keycloak 26.8 (guide « Importing and exporting realms ») confirme qu'il n'existe aucune option d'écrasement pour `start --import-realm` ; la commande `import --override` exige un serveur arrêté et le guide recommande de supprimer le realm avant de le réimporter. Le fichier JSON reste la seule source de vérité : `deploy/local/deploy.sh realm` rejoue l'import depuis lui.

La commande, relançable :

1. rend le realm (mots de passe de démonstration pris dans `local/.env`) et met à jour le Secret `keycloak-realm` ;
2. met Keycloak à 0 réplica, attend l'arrêt du pod ;
3. recrée la base PostgreSQL `keycloak` (`DROP DATABASE … WITH (FORCE)`, `CREATE DATABASE … OWNER keycloak`, `REVOKE ALL … FROM PUBLIC`, par le socket local du pod PostgreSQL)  : **toute la base revient à l'état du JSON** (realm `collector` : comptes, rôles, clients) **et du Secret `keycloak-admin`** (realm `master` et compte d'administration) ; sont perdues les sessions ouvertes et toute modification faite à la main dans la console. Si la commande échoue en cours de route, Keycloak est relancé à la sortie : relancer `deploy.sh realm` ;
4. remet Keycloak à 1 réplica, attend sa disponibilité et la configuration OpenID, puis affiche `scopes_supported`.

Elle ne s'exécute jamais toute seule : ni `infra` ni `all` ne la lancent (ils mettent seulement le Secret à jour). Sur un cluster neuf, le realm est importé au premier démarrage et `realm` est inutile. Alternative plus lourde : `cluster.sh delete`, `create`, puis `deploy.sh infra`.

## Le front : `https://app.127.0.0.1.sslip.io`

`deploy.sh services <tag>` (et `all <tag>`) déploie aussi l'image `ghcr.io/luucaaas/frontend:<tag>` avec **le même chart** que les services, configuré par `helm/values/frontend.yaml`. Ce qui change par rapport aux services, tout se lit dans ce fichier :

- nginx non root (uid 101), port 8080, sondes sur `/healthz` ; pas de Secret, pas de migration, pas de `ServiceMonitor` (nginx n'expose pas `/metrics`, limite acceptée) ;
- système de fichiers racine en lecture seule : `emptyDir` sur `/tmp` et sur `/etc/nginx/conf.d` (sortie des modèles `envsubst`, d'où `fsGroup: 101`) ;
- `config.json` (client OIDC, URL des API) vient d'un ConfigMap monté en lecture seule (`subPath`) : même image partout, un changement redémarre les pods (somme de contrôle en annotation) ;
- `CSP_CONNECT_SRC` (origines de l'API et de Keycloak de la CSP) est une variable d'environnement du ConfigMap `frontend-config` ;
- Ingress en mode `root` : hôte `app.`, chemin `/`, sans `Middleware` ;
- ressources adaptées à nginx (mesuré : 1 mC et 8 Mi par pod au repos) ; HPA de 2 à 5.
