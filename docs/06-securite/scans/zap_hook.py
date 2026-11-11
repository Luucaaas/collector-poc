"""Crochets de zap-api-scan.py (option --hook) : injection du jeton d'accès dans `Authorization`.

Le jeton n'est jamais en argument de commande ni dans ce fichier : run-scans.sh le donne au
conteneur par `docker run -e ZAP_ACCESS_TOKEN` (sans valeur sur la ligne de commande, Docker lit
l'environnement de l'appelant). Sans cette variable, le scan est anonyme et ce module ne fait rien.

Pourquoi un renouvellement : le jeton d'accès dure 5 minutes, un scan actif plus longtemps. Un fil
d'exécution échange le jeton de rafraîchissement (ZAP_REFRESH_TOKEN) toutes les 150 s contre un
nouveau jeton d'accès (Keycloak, client public `collector-web`) et remplace la règle de ZAP. Rien
n'est affiché : les journaux ne contiennent que le nombre de renouvellements.
"""

import contextlib
import json
import os
import ssl
import threading
import urllib.parse
import urllib.request
from typing import Any

TOKEN_URL = "https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect/token"
CA_FILE = "/ts/rootCA.pem"  # autorité de mkcert, montée par run-scans.sh
RULE = "collector-audit-bearer"
RENEW_EVERY_SECONDS = 150

_stop = threading.Event()
_stats = {"renewals": 0, "failures": 0}


def _set_token(zap: Any, access_token: str) -> None:
    """Pose (ou remplace) la règle « Replacer » qui fixe l'en-tête Authorization des requêtes."""
    # Première pose : la règle n'existe pas encore, la suppression échoue sans conséquence.
    with contextlib.suppress(Exception):
        zap.replacer.remove_rule(RULE)
    zap.replacer.add_rule(
        description=RULE,
        enabled="true",
        matchtype="REQ_HEADER",
        matchregex="false",
        matchstring="Authorization",
        replacement="Bearer " + access_token,
        initiators="",
    )


def _refresh(refresh_token: str) -> dict[str, Any]:
    body = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "client_id": "collector-web",
            "refresh_token": refresh_token,
        }
    ).encode()
    context = ssl.create_default_context(cafile=CA_FILE)  # vérification TLS jamais désactivée
    with urllib.request.urlopen(TOKEN_URL, data=body, timeout=15, context=context) as reply:
        payload: dict[str, Any] = json.load(reply)
        return payload


def _renew_loop(zap: Any, refresh_token: str) -> None:
    while not _stop.wait(RENEW_EVERY_SECONDS):
        try:
            fresh = _refresh(refresh_token)
            _set_token(zap, fresh["access_token"])
            refresh_token = fresh.get("refresh_token", refresh_token)
            _stats["renewals"] += 1
        except Exception as error:  # noqa: BLE001 : ne jamais faire tomber le scan, ni afficher de jeton
            _stats["failures"] += 1
            print("[hook] renouvellement du jeton en échec : " + type(error).__name__, flush=True)


def zap_started(zap: Any, target: str) -> None:
    access_token = os.environ.get("ZAP_ACCESS_TOKEN")
    if not access_token:
        print("[hook] scan anonyme (pas de jeton)", flush=True)
        return
    _set_token(zap, access_token)
    print("[hook] scan authentifié : en-tête Authorization posé par ZAP", flush=True)
    refresh_token = os.environ.get("ZAP_REFRESH_TOKEN")
    if refresh_token:
        threading.Thread(target=_renew_loop, args=(zap, refresh_token), daemon=True).start()


def zap_pre_shutdown(zap: Any) -> None:
    _stop.set()
    if os.environ.get("ZAP_ACCESS_TOKEN"):
        print(
            "[hook] renouvellements réussis : {renewals}, échecs : {failures}".format(**_stats),
            flush=True,
        )
