#!/usr/bin/env python3
"""Rend les fichiers de configuration qui contiennent des mots de passe (dossier `rendered/`).

- `collector-realm.json` : realm de base (`deploy/keycloak/`), marqueurs `${..._PASSWORD}`
  remplacés, plus le client de test `collector-tests` (pile docker compose seulement) ;
- `rabbitmq-definitions.json` : utilisateurs, vhost et permissions de RabbitMQ.

Usage : render.py <fichier .env> <dossier de sortie> [--cluster]. Bibliothèque standard seule.
Avec `--cluster` (deploy/local/deploy.sh), le client de test n'est pas ajouté et `collector-web`
n'accepte pas `http://localhost:5173` : le realm du cluster n'a ni Direct Access Grants ni adresse
de développement.
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REALM_USERS = ("ADMIN", "ALICE", "BOB", "CHLOE")

# Développement du front (`npm run dev`, Vite sur le port 5173) : adresse ajoutée au client public
# `collector-web` dans la pile docker compose seulement. Le realm du cluster reste limité à https://app.
DEV_FRONT_ORIGIN = "http://localhost:5173"

# Client de test : jetons sans navigateur (Direct Access Grants), avec l'audience collector-api.
# Il n'existe que dans la pile docker compose, jamais dans le realm de base.
TEST_CLIENT = {
    "clientId": "collector-tests",
    "name": "Tests d'acceptation : jetons sans navigateur (pile docker compose seulement)",
    "enabled": True,
    "publicClient": True,
    "standardFlowEnabled": False,
    "directAccessGrantsEnabled": True,
    "defaultClientScopes": [
        "web-origins",
        "acr",
        "roles",
        "basic",
        "collector-api-audience",
    ],
}


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def render_realm(env: dict[str, str], with_test_client: bool = True) -> str:
    text = (REPO / "deploy/keycloak/collector-realm.json").read_text()
    for user in REALM_USERS:
        text = text.replace("${" + user + "_PASSWORD}", env[user + "_PASSWORD"])
    if re.search(r"\$\{[A-Z]+_PASSWORD\}", text):
        raise SystemExit("Marqueur de mot de passe non remplacé dans le realm")
    realm = json.loads(text)
    if with_test_client:
        realm["clients"].append(TEST_CLIENT)
        for client in realm["clients"]:
            if client["clientId"] == "collector-web":
                client["redirectUris"].append(f"{DEV_FRONT_ORIGIN}/*")
                client["webOrigins"].append(DEV_FRONT_ORIGIN)
                attributes = client["attributes"]
                attributes["post.logout.redirect.uris"] += f"##{DEV_FRONT_ORIGIN}/*"
    return json.dumps(realm, indent=2, ensure_ascii=False) + "\n"


def render_rabbitmq(env: dict[str, str]) -> str:
    # Permissions (configure, write, read) par expressions régulières, limitées aux objets du POC.
    # AMQP : déclarer exige configure ; lier une file exige write sur la file et read sur
    # l'exchange ; consommer exige read sur la file ; publier exige write sur l'exchange.
    exchange = r"article\.events"
    queue = r"notification\.article-events"
    users = [
        ("admin", env["RABBITMQ_ADMIN_PASSWORD"], "administrator", (".*", ".*", ".*")),
        (
            "catalog",
            env["RABBITMQ_CATALOG_PASSWORD"],
            "",
            (f"^{exchange}$", f"^{exchange}$", "^$"),
        ),
        (
            "notification",
            env["RABBITMQ_NOTIFICATION_PASSWORD"],
            "",
            (f"^({exchange}|{queue})$", f"^{queue}$", f"^({exchange}|{queue})$"),
        ),
    ]
    definitions = {
        "vhosts": [{"name": "/"}],
        "users": [{"name": n, "password": p, "tags": t} for n, p, t, _ in users],
        "permissions": [
            {"user": n, "vhost": "/", "configure": c, "write": w, "read": r}
            for n, _, _, (c, w, r) in users
        ],
    }
    return json.dumps(definitions, indent=2) + "\n"


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--cluster"]
    cluster = len(args) != len(sys.argv) - 1
    env = read_env(Path(args[0]))
    out = Path(args[1])
    out.mkdir(parents=True, exist_ok=True)
    # Pile compose : lisible par les utilisateurs non-root des conteneurs. Cluster : les fichiers
    # contiennent des mots de passe et ne vont que dans des Secrets, donc dossier privé.
    out.chmod(0o700 if cluster else 0o755)
    for name, content in (
        ("collector-realm.json", render_realm(env, with_test_client=not cluster)),
        ("rabbitmq-definitions.json", render_rabbitmq(env)),
    ):
        target = out / name
        target.write_text(content)
        target.chmod(0o600 if cluster else 0o644)


if __name__ == "__main__":
    main()
