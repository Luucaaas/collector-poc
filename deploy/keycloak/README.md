# Realm Keycloak `collector`

`collector-realm.json` est le realm de base importé par Keycloak (`start --import-realm`) :

- rôles `buyer`, `seller`, `admin` ;
- client public `collector-web` (*Authorization Code* + PKCE, aucun *Direct Access Grants*) ;
- scope d'audience `collector-api` (mapper « Audience »), ajouté au jeton du client ;
- comptes `admin`, `alice` (`seller` et `buyer`), `bob` (`seller`), `chloe` (`buyer`).

**Aucun secret** : les mots de passe sont des marqueurs `${ADMIN_PASSWORD}`, `${ALICE_PASSWORD}`, `${BOB_PASSWORD}` et `${CHLOE_PASSWORD}`, remplacés au lancement par `deploy/compose/render.py` (pile `docker compose`) ou par le script de déploiement du cluster (phase 6).

**Pas de client de test ici.** Le client `collector-tests` (*Direct Access Grants*, qui permet aux tests d'acceptation d'obtenir un jeton sans navigateur) est ajouté seulement dans la pile `docker compose` par `render.py`. Il n'existe jamais sur le cluster : le flux *Resource Owner Password Credentials* est retiré par la RFC 9700 et reste une limite déclarée de la pile de test.
