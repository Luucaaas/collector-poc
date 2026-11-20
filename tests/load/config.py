"""Load test configuration: cluster addresses and passwords read from the environment.

Passwords are exported by `run.sh` into the environment of the Locust process only (read from
`deploy/local/.env`). They are never written or printed: when one is missing, the message names
the variable, never its value.
"""

import os

API_HOST = "https://api.127.0.0.1.sslip.io"
CATALOG = f"{API_HOST}/catalog/api/v1"
NOTIFICATION = f"{API_HOST}/notification/api/v1"
KEYCLOAK = "https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect"
CLIENT_ID = "collector-web"
REDIRECT_URI = "https://app.127.0.0.1.sslip.io/"


def ca_bundle() -> str | bool:
    """Authority that signs the cluster certificate (mkcert), provided by `run.sh`.

    Locust does not use the `REQUESTS_CA_BUNDLE` variable by itself: it is passed explicitly to the
    client. Without it, the value is `True`: verification against public authorities, so the
    mkcert certificate is refused. Never `False`: verification is never disabled.
    """
    return os.environ.get("REQUESTS_CA_BUNDLE") or True


def password_for(username: str) -> str:
    variable = f"LOAD_{username.upper()}_PASSWORD"
    value = os.environ.get(variable)
    if not value:
        raise RuntimeError(f"Environment variable {variable} missing or empty (see run.sh).")
    return value
