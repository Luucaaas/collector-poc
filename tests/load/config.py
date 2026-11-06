"""Configuration du test de charge : adresses du cluster et mots de passe lus dans l'environnement.

Les mots de passe sont exportés par `run.sh` dans l'environnement du seul processus Locust (lus dans
`deploy/local/.env`). Ils ne sont jamais écrits ni affichés : en cas d'absence, le message nomme la
variable, jamais sa valeur.
"""

import os

API_HOST = "https://api.127.0.0.1.sslip.io"
CATALOG = f"{API_HOST}/catalog/api/v1"
NOTIFICATION = f"{API_HOST}/notification/api/v1"
KEYCLOAK = "https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect"
CLIENT_ID = "collector-web"
REDIRECT_URI = "https://app.127.0.0.1.sslip.io/"


def ca_bundle() -> str | bool:
    """Autorité qui signe le certificat du cluster (mkcert), fournie par `run.sh`.

    Locust n'utilise pas la variable `REQUESTS_CA_BUNDLE` d'elle-même : on la passe explicitement au
    client. Sans elle, la valeur est `True` : vérification avec les autorités publiques, donc le
    certificat de mkcert est refusé. Jamais `False` : la vérification n'est jamais désactivée.
    """
    return os.environ.get("REQUESTS_CA_BUNDLE") or True


def password_for(username: str) -> str:
    variable = f"LOAD_{username.upper()}_PASSWORD"
    value = os.environ.get(variable)
    if not value:
        raise RuntimeError(f"Variable d'environnement {variable} absente ou vide (voir run.sh).")
    return value
