# Test de charge (Locust)

Mesure sur le cluster k3d l'indicateur **I3** (latence p95 en lecture et en publication, taux de réponses 5xx, 50 utilisateurs simultanés) et l'exigence **ENF-14** (p95 du délai entre l'événement et la notification). Définitions et seuils : [`docs/01-qualite/indicateurs.md`](../../docs/01-qualite/indicateurs.md) et [`docs/03-backlog/exigences.md`](../../docs/03-backlog/exigences.md). Hors CI : le test a besoin du cluster (`deploy/local/deploy.sh`), conformément à [`processus-test.md`](../../docs/01-qualite/processus-test.md).

## Lancer

```bash
tests/load/run.sh                         # 50 utilisateurs, montée de 1 par seconde, 6 minutes (environ 7 min 30 au total)
USERS=20 RUN_TIME=2m tests/load/run.sh    # essai court (variables : USERS, SPAWN_RATE, RUN_TIME)
```

Prérequis : cluster lancé et déployé, `uv`, `mkcert` (même autorité que celle du cluster), `kubectl` (contexte `k3d-collector`). Les mots de passe (lus dans `deploy/local/.env`) ne sont donnés qu'à la commande Locust, jamais exportés ni passés en argument. Le script sort avec le code 0 même si une mesure dépasse son seuil (pas de blocage, c'est un ticket de dette) ; il l'écrit alors clairement à l'écran et dans `resume.md`.

Chaque exécution crée `resultats/<AAAAMMJJ-HHMM>/`.

## Les fichiers

| Fichier | Rôle |
| --- | --- |
| `run.sh` | Orchestre tout : lit les mots de passe, vérifie l'API et Keycloak, relève l'environnement et l'HPA, lance Locust, interroge Prometheus, écrit `resume.md` |
| `locustfile.py` | Les scénarios : préparation de l'exécution, lecteurs anonymes, vendeurs connectés |
| `session.py` | Connexion à Keycloak (HTTP) et renouvellement du jeton |
| `auth.py` | Parties pures de la connexion : PKCE, lecture du formulaire et de la redirection, calendrier de renouvellement |
| `interests.py` | Calcul de la nouvelle liste des centres d'intérêt de chloe |
| `thresholds.py` | Seuils, lecture des CSV de Locust, rédaction de `resume.md` |
| `report.py` | Interroge Prometheus sur la fenêtre du plateau et appelle `thresholds` |
| `config.py` | Adresses et lecture des mots de passe dans l'environnement |
| `test_auth.py`, `test_interests.py`, `test_report.py` | Tests pytest sans réseau des parties pures |
| `pyproject.toml`, `uv.lock` | Projet uv (Python 3.12), `locust==2.47.0` figé |

Vérifications du projet : `cd tests/load && uv run ruff check . && uv run ruff format --check . && uv run mypy --strict . && uv run pytest`.

## Le scénario

- **Connexion** : comme la page web, par le flux Authorization Code + PKCE S256 du client public `collector-web` (page d'autorisation, formulaire de Keycloak, `code` lu sur la redirection, échange avec le `code_verifier`). Aucun client à mot de passe direct n'est ajouté à Keycloak. Le jeton d'accès dure 5 minutes : il est renouvelé par le jeton de rafraîchissement quand il lui reste moins d'une minute. La vérification TLS est active : l'autorité de mkcert est passée au client par `REQUESTS_CA_BUNDLE`, rien ne la désactive.
- **Préparation** (une fois) : `admin` crée la catégorie `Charge <date>` ; `chloe` retire de ses centres d'intérêt les catégories `Charge …` des exécutions précédentes (elle garde toutes les autres), ajoute celle-ci et active les deux préférences. Chaque publication et chaque changement de prix de l'exécution crée donc une notification pour chloe, ce qui alimente `notification_delay_seconds`.
- **Lecteurs anonymes (80 %, 40 utilisateurs sur 50)** : liste du catalogue (avec ou sans filtre de catégorie, pages de 20), liste des catégories, détail d'un article. Attente de 1 à 3 s entre deux actions, le temps de regarder un écran avant de cliquer (environ 20 requêtes par seconde au total).
- **Vendeurs (20 %, 10 utilisateurs)** : `alice` et `bob` à tour de rôle, une boutique par vendeur et par exécution, publication d'articles valides (201 `PUBLISHED`), une publication sur sept avec un numéro de téléphone (201 `REJECTED`, un succès métier), changement du prix de leurs articles. Attente de 4 à 10 s : saisir une annonce prend plus de temps que lire une page.
- **Noms de requêtes** : regroupés (`GET /articles`, `GET /articles/{id}`, `POST /articles`, `PUT /articles/{id}/price`), jamais un nom par identifiant. La connexion (`[connexion] …`) et la préparation (`[prépa] …`) ont leurs propres noms et sont exclues des seuils.

## Pourquoi ces paramètres

- **50 utilisateurs** : la charge nominale de l'indicateur I3.
- **Montée de 1 utilisateur par seconde** (50 s) : progressive, pour que les connexions des vendeurs (Keycloak calcule un hachage à chaque connexion) ne se bousculent pas et que l'HPA voie une charge qui augmente.
- **Plateau d'au moins 5 minutes** : l'option `--reset-stats` remet les statistiques à zéro quand les 50 utilisateurs sont lancés, donc la montée est exclue des mesures. Six minutes au total laissent environ 5 min 10 s de plateau : assez pour que les caches, les connexions et les JIT soient chauds, pour avoir plusieurs milliers de requêtes (un p95 stable) et pour couvrir au moins deux périodes d'évaluation de l'HPA (15 s) et un cycle de collecte de metrics-server.

## Lire `resume.md`

Un tableau de cinq mesures, chacune avec sa valeur, son seuil et un verdict (`conforme`, `non conforme` ou `non mesuré`) :

| Mesure | Seuil | Source |
| --- | --- | --- |
| Lecture du catalogue (`GET /articles`) | p95 < 300 ms | Locust |
| Publication d'article (`POST /articles`, valides et rejetées) | p95 < 500 ms | Locust |
| Réponses 5xx vues par Locust | < 1 % | Locust (toutes les requêtes de charge) |
| Réponses 5xx vues par les services | < 1 % | Prometheus (`http_requests_total`, hors sondes et `/metrics`) |
| Délai des notifications (ENF-14) | p95 < 2 s | Prometheus (`notification_delay_seconds`) |

Le résumé ajoute les autres requêtes (à titre indicatif), le détail par requête, la fenêtre de mesure, les images et digests déployés et l'état de l'HPA. Les autres fichiers du dossier : `locust_stats.csv`, `locust_failures.csv`, `locust_stats_history.csv`, `rapport.html`, `locust.log`, `fenetre.json` (début du plateau et fin), `hpa-avant.txt`, `hpa-evolution.txt` (toutes les 15 s), `hpa-apres.txt`. Aucun mot de passe ni jeton n'y figure, et `run.sh` remplace le nom de la machine par `<machine>` et le dossier personnel par `<home>` avant l'archivage.

## Limites

- **Locust tourne sur le même Mac que le cluster** et partage son processeur (10 CPU pour Docker Desktop, Locust en plus) : les latences mesurées incluent cette contention. À 50 utilisateurs, Locust lui-même est peu gourmand.
- **Les mesures traversent Traefik et TLS** (`https://api.127.0.0.1.sslip.io`), comme un vrai client : elles comprennent le chiffrement et le routage, pas seulement le service.
- **Données de démo créées à chaque exécution** : une catégorie, deux boutiques et quelques centaines d'articles, jamais supprimés. Elles s'accumulent et font grossir la liste du catalogue. Les centres d'intérêt de chloe ne grossissent pas : les catégories `Charge …` des exécutions précédentes sont retirées avant d'ajouter la nouvelle (limite métier de 20).
- **Le p95 de Prometheus** vient d'un histogramme à bornes fixes (2 s est une borne) : il est interpolé dans le seau, donc approximatif à l'intérieur d'un seau. Les 5xx côté services incluent le trafic qui ne vient pas de Locust sur la fenêtre (très faible sur un cluster de démonstration).
- **Un seul processus Locust** (pas de mode distribué) : suffisant pour 50 utilisateurs.
