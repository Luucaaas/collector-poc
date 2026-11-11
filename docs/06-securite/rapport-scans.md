# Rapport des scans de sécurité du POC (audit du 10/11/2026)

Audit reproductible du POC tel qu'il tourne sur le cluster k3d (images `sha-20e080b`) : OWASP ZAP (front, Keycloak, API), Trivy (images en amd64 et en arm64, configuration), SonarCloud, `npm audit`. Il **constate et qualifie**, il ne corrige rien : les corrections sont l'objet de P9-02, l'analyse de risques celui de P9-03, le plan de remédiation celui de P9-04.

Les rapports bruts sont dans [`scans/resultats/20261110-1641/`](scans/resultats/20261110-1641/) ; la synthèse chiffrée générée est `resume.md` dans ce dossier.

## 1. Versions, commande et périmètre

| Élément | Valeur |
| --- | --- |
| Commande exacte | `docs/06-securite/scans/run-scans.sh` (tout, environ 8 minutes ; étapes isolables : `run-scans.sh trivy sonar npm zap`) |
| Cible auditée | `catalog-service`, `notification-service`, `frontend` en `sha-20e080b` (digests dans `environnement.txt`), lus sur le cluster par le script |
| OWASP ZAP | 2.17.0, image officielle `zaproxy/zap-stable` (tag `20261026`, publiée le 26/10/2026, soit 15 jours avant l'audit), **épinglée par digest** `sha256:030d3df57735dacbb83464854758e674dd9ad01d79d12a129a8e58b1fd384238` (index amd64 + arm64), 2,35 Go sur le disque, conservée pour le rejeu |
| Trivy | 0.76.0 (celle de la CI), archive macOS arm64 vérifiée par SHA-256 `e7ec0d21fe842553f59af99aba2efbcc822369fbaed27019c575408b6d135fce`, dans un dossier temporaire supprimé en fin de script ; base de vulnérabilités du 10/11/2026 13:03 UTC (`environnement.txt`) |
| SonarCloud | API publique en lecture, sans jeton (projets `Luucaaas_collector-poc_catalog-service` et `…_notification-service`) |
| `npm audit` | npm 10.9.9, Node 22.23.4, sur `frontend/package-lock.json` (avec et sans les dépendances de développement) |
| Périmètre des scans actifs | **uniquement** `api.127.0.0.1.sslip.io` (le POC local). Front (`app.`) et Keycloak (`auth.`) : passif seulement. Aucun autre hôte |

**Vérification de la somme de Trivy.** La somme écrite dans la CI est celle de l'archive Linux. Pour le Mac, le script contrôle d'abord que le fichier de sommes de la release contient bien la somme Linux épinglée dans `backend.yml` (preuve que ce fichier est authentique), puis vérifie l'archive macOS avec lui. C'est une chaîne de confiance un peu plus faible que la somme épinglée dans le dépôt : si la montée de Trivy devient la norme sur Mac, épingler aussi la somme macOS.

## 2. Méthode

### 2.1 Comment le conteneur ZAP joint le cluster

Les noms `*.127.0.0.1.sslip.io` pointent vers `127.0.0.1`, qui, dans un conteneur, désigne le conteneur lui-même. Le script ajoute `--add-host <hôte>:host-gateway` pour `api.`, `app.` et `auth.` : ils se résolvent alors vers l'hôte Docker (le Mac), où k3d publie le port 443 de Traefik. Le certificat est celui de mkcert : le script copie le magasin de confiance Java de l'image, y ajoute l'autorité de mkcert (clé publique seulement) et le monte dans le conteneur (`-Djavax.net.ssl.trustStore`). **La vérification TLS n'est jamais désactivée.**

### 2.2 Comment le jeton passe à ZAP

1. `pkce_login.py` obtient les jetons d'`alice` (rôles `seller` et `buyer`) par le vrai flux *Authorization Code* + PKCE S256 du client `collector-web`, en réutilisant les fonctions de `tests/load/auth.py`. Le mot de passe est lu dans `deploy/local/.env` et donné à cette seule commande par variable d'environnement (jamais en argument).
2. Le script garde les deux jetons (accès et rafraîchissement) dans des variables du shell et les donne au conteneur par `docker run -e ZAP_ACCESS_TOKEN -e ZAP_REFRESH_TOKEN` **sans valeur sur la ligne de commande** : Docker lit l'environnement de l'appelant.
3. `zap_hook.py` (option `--hook` de `zap-api-scan.py`) pose une règle « Replacer » qui fixe l'en-tête `Authorization`, et la **renouvelle toutes les 150 s** avec le jeton de rafraîchissement : le jeton d'accès dure 5 minutes, un scan plus long ne perd pas sa session. Le renouvellement a été éprouvé à part, dans le même conteneur (réponse de Keycloak valable, nouveau jeton différent, `azp = collector-web`) ; il n'a pas été déclenché pendant les scans, qui durent 31 à 41 s (voir `zap-durees.txt`).
4. Rien n'est écrit : les jetons ne sont pas archivés, les rapports ZAP ne contiennent pas les requêtes complètes, et un masquage final remplace tout motif de jeton avant les compteurs (§ 6).

### 2.3 Passes ZAP

| Passe | Outil | Mode | Authentification |
| --- | --- | --- | --- |
| `front` | `zap-baseline.py` | passif (spider d'une minute, **sans soumission de formulaire**) | aucune |
| `keycloak` | `zap-baseline.py` | passif, depuis la page de connexion publique du realm `collector` | aucune |
| `api-catalog-anonyme`, `api-notification-anonyme` | `zap-api-scan.py` | **actif**, à partir de l'OpenAPI du service | aucune |
| `api-catalog-alice`, `api-notification-alice` | `zap-api-scan.py` | **actif**, même spécification | jeton d'`alice` |

Choix à connaître :

- **Une passe par service** : les OpenAPI des deux services sont distinctes et les routes publiques portent le préfixe `/catalog` ou `/notification` (retiré par Traefik), que la spécification ne connaît pas. Le script la complète d'un champ `servers` avant de la donner à ZAP, sans quoi ZAP aurait visé `/api/v1/…` (404).
- **Politique d'attaque complète.** Par défaut, `zap-api-scan.py` n'applique que la politique « API-Minimal » (quelques règles). Le script fournit un fichier de configuration minimal (`-c`), ce qui active **toutes** les règles actives de la politique par défaut (injections SQL de cinq familles, XSS, traversée de chemin, injection de commandes, SSRF, etc.), sauf la règle 40026 (voir § 3).
- **Durée maximale** d'une passe active : 12 minutes (`scanner.maxScanDurationInMins`) ; en pratique 31 à 41 s, car l'API est petite (16 et 11 URL importées).

### 2.4 Trivy, SonarCloud, `npm audit`

- **Images** : `trivy image --image-src remote --platform linux/{amd64,arm64} --scanners vuln,secret`, toutes sévérités, **sans `--ignore-unfixed`** (la CI, elle, l'utilise : voir les écarts en § 4). `--image-src remote` lit l'image sur GHCR sans rien tirer dans Docker.
- **Configuration** : `trivy config` sur `deploy/` (manifestes de l'infrastructure, de Traefik et de la vérification), sur les Dockerfiles des services, sur le Dockerfile du front, et sur le **chart Helm rendu** par `helm template` avec les mêmes values que `deploy.sh`.
- **SonarCloud** : issues ouvertes, *security hotspots* (et leur statut), état de la *quality gate*.
- **`npm audit`** complet puis `--omit=dev`.

## 3. Difficultés rencontrées (à garder pour l'oral)

1. **Un premier scan actif a saturé le cluster.** Sans plafond, le conteneur ZAP a pris environ 430 % de CPU et 4,8 Gio sur les 7,75 Gio de la machine virtuelle de Docker Desktop, qui sert aussi le cluster : PostgreSQL, Keycloak, Grafana, Prometheus, le front et les services sont passés en `CrashLoopBackOff` pendant environ trois minutes. J'ai arrêté le scan ; le cluster est revenu seul à l'état sain (aucune intervention, `smoke.sh` 18/18). La cause directe est la règle « XSS basé sur le DOM » (40026), qui lance un navigateur Firefox dans le conteneur : inutile sur une API JSON, elle est désormais désactivée, et le conteneur est plafonné (`--memory 2g --cpus 2`, tas Java 1 Gio). Les compteurs de redémarrage de `pods-avant.txt` (jusqu'à 5 selon le pod, contre 0 avant l'incident) en gardent la trace ; l'exécution de cet incident n'est pas archivée. C'est aussi un constat de résilience (F-24).
2. **Le scan « passif » de Keycloak soumettait le formulaire de connexion.** Deux premiers essais ont envoyé le formulaire (vide) du realm : une tentative d'authentification, sans compte visé, qui n'a rien verrouillé (la connexion d'`alice` a réussi ensuite) mais qui n'est pas « passif ». `spider.postform=false` ne suffit pas : en mode par défaut (Automation Framework), ZAP ignore l'option. Il faut `--autooff`. Vérifié sur un serveur local jetable qui compte les requêtes : 2 POST sans `--autooff`, 0 avec ; dans le rapport final, toutes les requêtes du scan passif sont des GET.
3. **Les rapports ZAP recopient des URL de Keycloak** qui contiennent un paramètre `client_data` encodé en base64 : le masquage des jetons l'a remplacé par `<jeton-masqué>` (il ne s'agit pas d'un jeton, mais le masquage préfère le faux positif).
4. **Les corps JSON ne sont fuzzés qu'en partie** (voir les limites, § 8).

## 4. Résultats chiffrés

### 4.1 Tableau résumé

| Outil | Cible | Critique | Haute | Moyenne | Basse | Informatif |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ZAP | front (passif) | 0 | 0 | 2 | 4 | 5 |
| ZAP | Keycloak (passif) | 0 | 0 | 5 | 7 | 6 |
| ZAP | API catalog, sans jeton (actif) | 0 | 0 | 0 | 3 | 5 |
| ZAP | API catalog, alice (actif) | 0 | 0 | 0 | 3 | 4 |
| ZAP | API notification, sans jeton (actif) | 0 | 0 | 0 | 1 | 4 |
| ZAP | API notification, alice (actif) | 0 | 0 | 0 | 3 | 4 |
| Trivy, images (lignes, toutes) | `catalog-service`, `notification-service` (identiques, chacune en amd64 et arm64) | 0 | 49 | 82 | 66 | 0 |
| Trivy, images (lignes, toutes) | `frontend` (amd64 et arm64) | 0 | 0 | 1 | 0 | 0 |
| Trivy, secrets | les trois images | 0 | 0 | 0 | 0 | 0 |
| Trivy, configuration | Dockerfiles, `deploy/`, chart rendu (59 constats) | 0 | 7 | 18 | 34 | 0 |
| SonarCloud | `catalog-service` et `notification-service` | 0 | 0 | 2 (majeures, mauvaises pratiques de code) | 0 | 0 |
| SonarCloud, *security hotspots* | idem | 0 | 0 | 0 | 0 | 0 |
| `npm audit` (développement compris) | `frontend` | 0 | 0 | 10 | 0 | 0 |
| `npm audit --omit=dev` | `frontend` (ce qui est dans l'image) | 0 | 0 | 0 | 0 | 0 |

**Aucune vulnérabilité critique, aucun secret, aucun *security hotspot*, et aucune alerte de niveau élevé (ZAP) dans le POC.** Les deux *quality gates* SonarCloud sont au vert. Le scan actif n'a révélé aucune injection, XSS ni contournement d'authentification ; la seule alerte de niveau moyen concerne les en-têtes CSP (front et Keycloak).

### 4.2 Vulnérabilités sans correctif, par image et par architecture

C'est l'action d'I4 « compter les vulnérabilités sans correctif », jamais mesurée jusqu'ici (la CI utilise `--ignore-unfixed`). Les nombres sont des **lignes** (paquet, version, CVE), comme dans les tableaux de Trivy ; entre parenthèses, le nombre de **CVE distinctes** (un même identifiant touche souvent plusieurs paquets d'un même projet, par exemple 9 paquets d'util-linux).

| Image | Arch. | Système | Total des lignes | Avec correctif | **Sans correctif** | dont HIGH | dont MEDIUM | dont LOW | CRITICAL |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `catalog-service` | amd64 | Debian 13.7 | 197 | 11 | **186** (84 CVE) | 47 (11 CVE) | 74 (38 CVE) | 65 (35 CVE) | 0 |
| `catalog-service` | arm64 | Debian 13.7 | 197 | 11 | **186** (84 CVE) | 47 (11 CVE) | 74 (38 CVE) | 65 (35 CVE) | 0 |
| `notification-service` | amd64 | Debian 13.7 | 197 | 11 | **186** (84 CVE) | 47 (11 CVE) | 74 (38 CVE) | 65 (35 CVE) | 0 |
| `notification-service` | arm64 | Debian 13.7 | 197 | 11 | **186** (84 CVE) | 47 (11 CVE) | 74 (38 CVE) | 65 (35 CVE) | 0 |
| `frontend` | amd64 | Alpine 3.24.2 | 1 | 1 | **0** | 0 | 0 | 0 | 0 |
| `frontend` | arm64 | Alpine 3.24.2 | 1 | 1 | **0** | 0 | 0 | 0 | 0 |

- **L'arm64 donne exactement les mêmes résultats que l'amd64** (même nombre, mêmes identifiants) pour les trois images : l'arm64 des services, jamais scanné jusqu'ici, ne cache rien de plus.
- Les 186 lignes sont du système Debian de l'image de base (`python:3.12-slim`) ; leur statut est `affected` (184) ou `fix_deferred` (2) : Debian n'a pas publié de correctif. Les 11 CVE HIGH touchent `util-linux` (`mount`, `login`, `bsdutils`…), `libsqlite3-0`, `libsystemd0`, `libacl1`, `ncurses` et `perl-base`.
- Les **11 lignes avec correctif** par image sont, elles, à corriger (F-01 à F-03) : la CI ne les a pas arrêtées. Hypothèse, non vérifiée : les avis sont postérieurs à la construction de l'image, et le job `publish` du backend ne rescanne pas.

### 4.3 Écart avec les contrôles de la CI

Le seuil de la CI (`CRITICAL,HIGH --ignore-unfixed`) appliqué aujourd'hui aux images des services donnerait **2 constats HIGH par service** (`zlib1g`, F-01), alors que la CI de la construction était verte : une image publiée vieillit. C'est l'argument pour un **scan planifié des images déployées** (proposition pour P9-04), pas seulement à la construction.

## 5. Constats qualifiés

Légende de la qualification : **VPC** vrai positif à corriger ; **VPA** vrai positif accepté (avec la raison) ; **FP** faux positif (avec la preuve) ; **Lxx** déjà couvert par une limite de `architecture-poc.md` § 8. Les preuves citent le fichier de `scans/resultats/20261110-1641/` et la ligne (fichiers `.txt` de Trivy et `.md` de ZAP) ou le champ (fichiers `.json`).

| Id | Outil | Composant | Constat | Sévérité (outil) | Qualification | Preuve |
| --- | --- | --- | --- | --- | --- | --- |
| F-01 | Trivy | `catalog-service`, `notification-service` (amd64 et arm64) | `zlib1g` 1:1.3.dfsg+really1.3.1-1+b1 : CVE-2026-76844 et CVE-2026-85091 (HIGH), CVE-2026-27171 (MEDIUM) ; corrigé par `…+deb13u1` | HIGH | **VPC** : reconstruire l'image avec les paquets à jour (`apt-get upgrade` dans l'étage final ou base plus récente épinglée par digest) | `trivy-catalog-service-amd64.txt:719`, `:723` ; `trivy-notification-service-amd64.txt:719` ; arm64 identique |
| F-02 | Trivy | `catalog-service`, `notification-service` | `PyJWT` 2.14.0 : CVE-2026-101918 et CVE-2026-102275 (MEDIUM), corrigés en 2.15.0. **Bibliothèque de vérification des jetons** (S3) | MEDIUM | **VPC** : monter `PyJWT` à 2.15.0 dans les deux `uv.lock`, relancer les tests (couverture et acceptation) | `trivy-catalog-service-amd64.txt:739`, `:743` ; `trivy-notification-service-amd64.txt:739` |
| F-03 | Trivy | `catalog-service`, `notification-service` | `pip` 25.0.1 présent dans l'image d'exécution : 5 MEDIUM et 1 LOW, corrigés en 25.3 à 26.2.0. `pip` ne sert pas à l'exécution | MEDIUM | **VPC** : retirer `pip` de l'étage final (ou le mettre à jour) | `trivy-catalog-service-amd64.txt:747` à `:766` ; `trivy-notification-service-amd64.txt:747` |
| F-04 | Trivy | `catalog-service`, `notification-service` | **186 lignes sans correctif** (84 CVE : 11 HIGH, 38 MEDIUM, 35 LOW), système Debian 13.7, identiques en amd64 et arm64 (§ 4.2) | HIGH au pire | **VPA** : aucun correctif publié par Debian ; ces paquets (`util-linux`, `libsystemd0`, `libsqlite3-0`…) ne sont pas appelés par l'application ; la surface est réduite par S7 (utilisateur non root, système de fichiers en lecture seule, capacités retirées). Analyse CVE par CVE non faite. À suivre au plan (base minimale, scan planifié) | `trivy-catalog-service-amd64.txt:4` (`Total: 189`), `trivy-notification-service-amd64.txt:4`, `resume.md` (tableau des images) |
| F-05 | Trivy | `frontend` | `zlib` 1.3.2-r1 : CVE-2026-4738 (MEDIUM), « corrigé » en 1.4-r0 selon Alpine | MEDIUM | **FP probable** : la description de la CVE vise `OSGeo gdal` avant 3.11.0 (modules `infback9` embarqués), pas la `zlib` d'Alpine ; une reconstruction qui embarque 1.4-r0 le fait disparaître sans coût | `trivy-frontend-amd64.txt:9` ; `trivy-frontend-amd64.json` (champ `Description`) |
| F-06 | ZAP | Keycloak (`auth.`) | La console d'administration (`/admin/master/console/`) répond 200 sur l'hôte public | Informatif (découverte du spider) | **Déjà couvert par L19 (Haute)** ; **proposé pour P9-02** (n'exposer que `/realms/` et `/resources/` sur l'hôte public) | `zap-keycloak.md:146` |
| F-07 | ZAP | API (`api.`) et Keycloak (`auth.`) | `Strict-Transport-Security` absent (sur toutes les réponses de l'API et de Keycloak) ; `X-Content-Type-Options` et `Cross-Origin-Resource-Policy` absents des réponses 200 de l'API (uvicorn les envoie sans) ; le front (nginx) a HSTS et `nosniff` (aucune de ces deux alertes sur le front) | Basse | **VPC** (faible coût) : middleware d'en-têtes de Traefik sur `api.` et `auth.` | `zap-api-catalog-anonyme.md:44` à `:46` ; `zap-api-catalog-alice.md:44` à `:46` ; `zap-api-notification-alice.md:44` à `:46` ; `zap-api-notification-anonyme.md:40` ; `zap-keycloak.md:54` |
| F-08 | ZAP | front (`app.`) | CSP : `img-src 'self' https: data:` accepte les images de n'importe quelle origine HTTPS (« Wildcard Directive »). Le code du front n'affiche aucune image (aucun `<img`, `Avatar` ni `CardMedia` dans `frontend/src`) | Moyenne | **VPC** (faible coût) : resserrer à `img-src 'self' data:` dans le modèle nginx | `zap-front.md:39` ; `zap-front.json` (champ `evidence`) |
| F-09 | ZAP | front et Keycloak | CSP : `style-src 'unsafe-inline'` (front) ; `unsafe-inline` des scripts et des styles, absence de repli, `*` (Keycloak) | Moyenne | Front : **déjà couvert par L24** (Emotion). Keycloak : **VPA**, produit tiers qui pose lui-même ses en-têtes | `zap-front.md:40` ; `zap-keycloak.md:44` à `:47` |
| F-10 | ZAP | front, Keycloak, API | `Cross-Origin-Embedder-Policy`, `Cross-Origin-Opener-Policy` et `Cross-Origin-Resource-Policy` absents | Basse | **VPA** : isolation d'origine croisée contre les attaques de type Spectre, sans enjeu pour ce POC (aucun contenu sensible servi aux autres origines) ; à reprendre avec F-07 pour la CORP | `zap-front.md:41` à `:43` ; `zap-keycloak.md:50` à `:52` ; `zap-api-notification-alice.md:44` |
| F-11 | ZAP | front | « Timestamp Disclosure » et « Suspicious Comments » dans `assets/index-*.js` | Basse, informatif | **FP** : l'entier détecté est `1540483477`, une constante d'une bibliothèque embarquée (pas un horodatage du serveur) ; le « commentaire suspect » est du code compilé qui contient le mot `admin` (rôle `admin` de l'interface) | `zap-front.md:44`, `:45` ; `zap-front.json` (champs `evidence`, `otherinfo`) |
| F-12 | ZAP | Keycloak | Absence de jeton anti-CSRF ; cookies `KC_AUTH_SESSION_HASH` sans `HttpOnly` et `AUTH_SESSION_ID` avec `SameSite=None` ; `Permissions-Policy` absent | Moyenne, Basse | **FP** pour l'anti-CSRF (le formulaire est protégé par le `session_code` et l'`execution` de l'URL, relevés par ZAP lui-même) ; **VPA** pour les cookies et l'en-tête (comportement standard de Keycloak ; `KC_AUTH_SESSION_HASH` est lu par le JavaScript de Keycloak, `SameSite=None` sert le flux de redirection) | `zap-keycloak.md:43`, `:48`, `:49`, `:53` |
| F-13 | ZAP | front, Keycloak, API | Alertes informatives : cache (« Non-Storable », « Re-examine Cache-control »), 170 à 218 réponses 4xx (le scan envoie des requêtes invalides, c'est normal), « User Agent Fuzzer », « Modern Web Application », « Session Management Response » | Informatif | **Non retenues** (aucun risque) | `zap-front.md:46` à `:49` ; `zap-api-catalog-anonyme.md:47` à `:51` |
| F-14 | Trivy | RabbitMQ | Conteneur en root, sans `securityContext` : système de fichiers racine inscriptible, élévation de privilèges possible, capacités par défaut, profil seccomp absent (3 HIGH, 3 MEDIUM, 7 LOW) | HIGH | **Déjà couvert par L17 et L18** | `trivy-config-deploy.txt:190` |
| F-15 | Trivy | Keycloak | Système de fichiers racine non en lecture seule (HIGH), UID et GID 1000 (≤ 10000), CPU non limité, registre `quay.io` | HIGH | Lecture seule : **déjà couvert par L17**. Le reste (UID, CPU) : **VPA** (faible) | `trivy-config-deploy.txt:2` |
| F-16 | Trivy | PostgreSQL | UID et GID 70 (≤ 10000), CPU non limité (3 LOW) | LOW | **VPA** : l'UID 70 est celui de l'image officielle `postgres:alpine` ; le CPU non limité relève de F-24 | `trivy-config-deploy.txt:121` |
| F-17 | Trivy | chart Helm rendu | « Registre non fiable » (`ghcr.io`, `quay.io`) : règle `KSV-0125`, 5 occurrences | MEDIUM | **FP** : la règle compare à une liste de registres propre à Trivy ; chaque image est épinglée par digest et vérifiée sur le registre avant tout déploiement (`deploy.sh`) | `trivy-config-helm-rendu.txt:54` ; `trivy-config-deploy.txt:2` |
| F-18 | Trivy | `deploy/k8s/traefik-config.yaml` | Ressource utilisateur placée dans `kube-system` (`KSV-0037`, 2 occurrences) | MEDIUM | **FP** : le `HelmChartConfig` de Traefik, fourni par k3s, doit se trouver dans `kube-system` pour être pris en compte | `trivy-config-deploy.txt:469` |
| F-19 | Trivy | `deploy/k8s/whoami-verif.yaml` | 18 constats (root, système de fichiers inscriptible, limites…) | HIGH (3) | **FP** : ressource temporaire de `cluster.sh verify`, supprimée à la fin de la vérification ; absente du cluster déployé | `trivy-config-deploy.txt:502` ; en-tête du fichier |
| F-20 | Trivy | chart Helm rendu | `KSV-01010` « ConfigMap with sensitive content » (2) ; `KSV-0110` « espace de noms par défaut » (4) | MEDIUM, LOW | **FP** : la clé signalée est `LOG_LEVEL` (valeur `INFO`) ; l'espace de noms `default` vient de `helm template` lancé sans `-n` alors que `deploy.sh` installe dans `collector` | `trivy-config-helm-rendu.txt:7`, `:15` |
| F-21 | Trivy | front (chart rendu) | UID et GID 101 (≤ 10000) (2 LOW) | LOW | **VPA** : imposé par l'image `nginx-unprivileged` (utilisateur non root) | `trivy-config-helm-rendu.txt` (entrée `frontend.yaml`) |
| F-22 | Trivy | les trois Dockerfiles | Pas d'instruction `HEALTHCHECK` (`DS-0026`) | LOW | **VPA** : Kubernetes n'utilise pas le `HEALTHCHECK` de Docker, il a ses sondes (`/health/live`, `/health/ready`) | `trivy-config-dockerfiles.txt:7` ; `trivy-config-frontend.txt:7` |
| F-23 | SonarCloud | `catalog-service`, `notification-service` | `python:S9152` (MAJOR, mauvaise pratique) : le nettoyage après le `yield` du *lifespan* peut être sauté en cas de sortie anticipée | MAJOR | **VPC** (mineur, maintenabilité et non sécurité) : `try/finally` autour du `yield` ; la *quality gate* reste verte | `sonar-catalog-service-issues.json` (`src/catalog/main.py`, ligne 33) ; `sonar-notification-service-issues.json` (ligne 31) |
| F-24 | Observation | cluster (infrastructure) | Une saturation de la machine virtuelle de Docker Desktop (provoquée par ZAP, § 3) met PostgreSQL, Keycloak et d'autres pods en `CrashLoopBackOff` ; reprise automatique en quelques minutes, sans perte constatée. Aucune requête ni limite de CPU sur PostgreSQL, Keycloak et RabbitMQ | (hors outil) | **VPC pour le plan** : *requests* et *limits* sur l'infrastructure ; recoupe L3, L8, L9 | `pods-avant.txt` (compteurs de redémarrage jusqu'à 5, 0 avant l'incident) ; `trivy-config-deploy.txt` (`KSV-0011`) |
| F-25 | `npm audit` | `frontend` (outillage de développement) | `minimatch` 7.0.0 à 11.0.0, avis GHSA-g3hv-75wg-m249, et les 9 paquets qui en dépendent (chaîne ESLint) : 10 vulnérabilités modérées ; correction proposée : `eslint` en version majeure | MEDIUM | **VPA** : outillage qui n'entre pas dans l'image (`npm audit --omit=dev` : 0) ; à traiter au plan | `npm-audit-complet.json` (`vulnerabilities.minimatch`), `npm-audit-prod.json` (0) |

Répartition des 25 constats par qualification principale : **vrai positif à corriger** 7 (F-01, F-02, F-03, F-07, F-08, F-23, et F-24 pour le plan) ; **vrai positif accepté** 6 (F-04, F-10, F-16, F-21, F-22, F-25) ; **mixtes** 3 (F-09 : L24 pour le front et accepté pour Keycloak ; F-12 : faux positif pour l'anti-CSRF et accepté pour les cookies ; F-15 : L17 pour la lecture seule et accepté pour le reste) ; **faux positifs** 6 (F-05, F-11, F-17, F-18, F-19, F-20) ; **déjà couverts par une limite** 2 (F-06 par L19, F-14 par L17 et L18) ; **non retenu** 1 (F-13, informatif).

## 6. Ce qui est archivé : compteurs

Le script masque, dans tout ce qui est archivé, les motifs de jetons, le nom de la machine et le dossier personnel, puis compte les occurrences. Résultat de l'exécution du 10/11/2026 16:41, sur `scans/resultats/20261110-1641/` **et** sur les scripts :

| Compteur | Valeur |
| --- | ---: |
| Jetons (début d'un JWT) | 0 |
| Fichiers contenant un mot de passe ou un secret lu dans `deploy/local/.env` | 0 |
| Nom de la machine | 0 |
| Dossier personnel | 0 |

## 7. Résultats de charge vus sous l'angle sécurité

Le protocole 5 (`docs/04-experimentations/05-charge-disponibilite/`) a démontré la **disponibilité** : pic de 200 utilisateurs, HPA de 2 à 5 réplicas en 60 s, pod supprimé remplacé en 4,9 s, 0 réponse 5xx sur 20 235. Sous l'angle de la sécurité, c'est une défense contre l'indisponibilité subie, pas contre l'indisponibilité provoquée : **il n'y a aucune limitation de débit** (L6). Un attaquant qui envoie la charge de Locust sans compte consomme les ressources du cluster jusqu'à la mise à l'échelle maximale (5 réplicas par service), après quoi les requêtes se dégradent ; et rien ne limite les tentatives de connexion répétées sur Keycloak (détection de force brute non activée, non éprouvée par cet audit : elle n'était pas dans le périmètre actif). Le scan actif lui-même (un conteneur plafonné à 2 CPU) a suffi à faire monter `catalog-service` à 4 réplicas pendant l'audit (`hpa-avant.txt` : 4 au départ de la dernière exécution, `hpa-apres.txt` : 3 à la fin, retour progressif à 2) : le HPA réagit, mais la charge d'un seul poste suffit à le faire réagir. Constat cohérent avec L6 (priorité Moyenne) ; à reprendre dans l'analyse de risques (P9-03).

## 8. Limites de l'audit

- **Pas de passe en tant qu'`admin`.** Le scan authentifié utilise `alice` (`seller` et `buyer`) : la route `POST /categories` (rôle `admin`) n'a été vue qu'avec un 403 et un 401. Le contrôle de rôle est testé par les tests d'acceptation, pas par cet audit.
- **Les corps JSON ne sont fuzzés qu'en partie.** ZAP fabrique un corps pour chaque `POST` et `PUT` à partir de la spécification, mais les champs qui exigent une valeur précise (identifiants existants, prix, catégorie) sont refusés par la validation (422 : 170 à 218 réponses 4xx par passe). C'est un bon signe pour la validation, mais le scan n'a pas atteint les traitements métier derrière. Aucune donnée n'a été créée par le scan (une seule catégorie existe, celle du jeu de démonstration).
- **Le front n'est pas scanné activement** (passif seulement) et ZAP ne sait pas parcourir une application monopage sans le *spider* AJAX (non lancé : il demande un navigateur, voir § 3). Les parcours du front sont couverts par Playwright, pas par ZAP.
- **Keycloak** est un produit tiers : passif seulement, et la page analysée est celle de la connexion. Rien n'a été tenté sur la protection contre la force brute.
- **La CI ne contient pas ZAP** (L13) : cet audit est ponctuel, sur le cluster local, non rejoué à chaque livraison.
- **Les vulnérabilités sans correctif ne sont pas analysées une à une** : l'acceptation de F-04 repose sur l'absence de correctif et sur les mesures de S7, pas sur une démonstration de non-exploitabilité.
- **Un seul jeu de données** : la base de vulnérabilités de Trivy est celle du 10/11/2026 13:03 UTC ; elle évolue toutes les six heures, d'où l'intérêt d'un scan planifié (§ 4.3).

## 9. Conclusion : ce qui part en P9-02 et au plan

### 9.1 Proposé pour P9-02 (corrections dans le POC, faible coût)

| Id | Correction | Fichiers probables |
| --- | --- | --- |
| F-01 | Reconstruire les images des services avec les paquets Debian à jour (`zlib1g`) | `services/*/Dockerfile` |
| F-02 | `PyJWT` 2.15.0 dans les deux services, tests de non-régression | `services/*/pyproject.toml`, `uv.lock` |
| F-03 | Retirer `pip` de l'étage final des services | `services/*/Dockerfile` |
| F-06 | N'exposer sur `auth.` que `/realms/` et `/resources/` (console d'administration retirée de l'hôte public), si l'accès administrateur reste possible autrement (`port-forward`) | `deploy/infra/keycloak.yaml` (Ingress) |
| F-07 | En-têtes de sécurité (HSTS, `nosniff`, CORP) sur `api.` et `auth.` par un middleware Traefik | `deploy/helm/…`, `deploy/infra/keycloak.yaml` |
| F-08 | `img-src 'self' data:` | `frontend/nginx/` (modèle de CSP), tests e2e (violation de CSP) |
| F-23 | `try/finally` autour du `yield` du *lifespan* | `services/*/src/*/main.py` |

### 9.2 Pour le plan de remédiation (P9-04)

- **F-04** : 186 vulnérabilités sans correctif par service (84 CVE) : changer de base (image plus petite, sans les outils système), **scan planifié des images déployées** non bloquant, avec rapport archivé (§ 4.3).
- **F-14, F-15** (L17, L18) : sécuriser RabbitMQ et Keycloak (`securityContext`, lecture seule).
- **F-06** (L19) : séparer la console d'administration du domaine public, restreindre les appelants (NetworkPolicies, L4).
- **F-24** : *requests* et *limits* sur l'infrastructure ; recoupe L3, L8, L9.
- **F-25** : monter ESLint (changement majeur), en branche d'essai.
- **F-10** : en-têtes COOP/COEP/CORP sur le front, si le plan retient la défense en profondeur.
- **L6** (§ 7) : limitation de débit et détection de force brute.
- **L13** : ZAP et Trivy planifié dans la CI.
- Reprendre **F-09** (L24, CSP à *nonce*).

Aucune correction n'a été faite dans cette tâche. Le cluster est resté sain (`smoke.sh` 18/18 avant et après, voir `scans/resultats/20261110-1641/`).
