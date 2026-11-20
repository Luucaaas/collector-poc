#!/usr/bin/env python3
"""Renders the configuration files that contain passwords (`rendered/` directory).

- `collector-realm.json`: base realm (`deploy/keycloak/`), `${..._PASSWORD}` markers
  replaced, plus the `collector-tests` test client (docker compose stack only);
- `rabbitmq-definitions.json`: RabbitMQ users, vhost and permissions.

Usage: render.py <.env file> <output directory> [--cluster]. Standard library only.
With `--cluster` (deploy/local/deploy.sh), the test client is not added and `collector-web`
does not accept `http://localhost:5173`: the cluster realm has neither Direct Access Grants nor a
development address.
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REALM_USERS = ("ADMIN", "ALICE", "BOB", "CHLOE")

# Front-end development (`npm run dev`, Vite on port 5173): address added to the public client
# `collector-web` in the docker compose stack only. The cluster realm stays limited to https://app.
DEV_FRONT_ORIGIN = "http://localhost:5173"

# Test client: tokens without a browser (Direct Access Grants), with the collector-api audience.
# It only exists in the docker compose stack, never in the base realm.
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
        raise SystemExit("Password marker not replaced in the realm")
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
    # Permissions (configure, write, read) by regular expressions, limited to the POC's objects.
    # AMQP: declaring requires configure; binding a queue requires write on the queue and read on
    # the exchange; consuming requires read on the queue; publishing requires write on the exchange.
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
    # Compose stack: readable by the containers' non-root users. Cluster: the files
    # contain passwords and only go into Secrets, so a private directory.
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
