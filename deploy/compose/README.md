# Pile docker compose

Pile locale du POC, pour développer, lancer les tests d'acceptation et alimenter le job `acceptance` de la CI (phase 5).

```bash
./up.sh               # construit les images des services et démarre (délai borné : WAIT_TIMEOUT, 300 s)
./up.sh --no-build    # utilise CATALOG_IMAGE et NOTIFICATION_IMAGE déjà chargées (CI : docker load)
./down.sh             # arrête, garde les données
./down.sh --volumes   # arrête et supprime les volumes PostgreSQL et RabbitMQ
```

## Contenu

Les images d'infrastructure sont épinglées par digest dans `compose.yaml` (`tag@sha256:…`, digest de l'index multi-architecture) : le tableau ne montre que le tag, lisible ; le digest fait foi.

| Service | Image | Port publié (127.0.0.1) | Remarques |
| --- | --- | --- | --- |
| `postgres` | `postgres:18.4-alpine` | aucun | bases `catalog_db`, `notification_db`, `keycloak`, un propriétaire sans droit de superutilisateur par base, accès `PUBLIC` retiré (`postgres-init/10-roles.sh`, au premier démarrage d'un volume vide) |
| `rabbitmq` | `rabbitmq:4.3.5-management` | 5672 (AMQP), 15672 (management) | utilisateurs `admin`, `catalog`, `notification` créés depuis `rendered/rabbitmq-definitions.json` ; pas de `guest` |
| `keycloak` | `quay.io/keycloak/keycloak:26.8.0` | 8080 | `start --import-realm`, sur PostgreSQL ; `KC_HOSTNAME=http://localhost:8080`, donc `iss` vaut toujours `http://localhost:8080/realms/collector` ; sonde : `GET /realms/collector/.well-known/openid-configuration` sur 8080, qui répond 200 une fois le realm importé (la santé du port 9000 se déclare prête trop tôt) |
| `catalog-migrate`, `notification-migrate` | image du service | aucun | `alembic upgrade head`, puis sortie ; le service attend `service_completed_successfully` |
| `catalog` | `collector/catalog-service:local` | 8001 | sonde `/health/ready` (Python et `urllib`, aucun outil ajouté à l'image) |
| `notification` | `collector/notification-service:local` | 8002 | idem |

Les services lisent les clés JWKS par `http://keycloak:8080` (réseau interne) mais vérifient `iss` avec l'URL publique.

## Secrets

`up.sh` crée `.env` à partir de `.env.example` (chaque `change-me` devient un mot de passe aléatoire du module `secrets`, droits 600) et ne l'écrase jamais. Puis `render.py` écrit dans `rendered/` (ignoré par git) :

- `collector-realm.json` : le realm de base de [`../keycloak/`](../keycloak/) (marqueurs `${..._PASSWORD}` remplacés) **plus le client de test `collector-tests`** ;
- `rabbitmq-definitions.json` : utilisateurs et permissions.

## Limites déclarées

- **Client de test** : `collector-tests` active le flux *Resource Owner Password Credentials* (*Direct Access Grants*), retiré par la RFC 9700. Il n'existe que dans cette pile et jamais dans le realm de base ni sur le cluster.
- **Permissions RabbitMQ** : limitées par expressions régulières aux objets du POC (`article.events`, `notification.article-events`), dans le vhost `/`. Seul `admin` a des droits larges ; il sert aux tests (file temporaire) et au management.
- **HTTP en clair**, ports sur `127.0.0.1` uniquement : le TLS arrive avec le cluster (phase 6).
- Keycloak en mode `start` sur HTTP, avec un nom d'hôte fixé : pas de configuration de production.
