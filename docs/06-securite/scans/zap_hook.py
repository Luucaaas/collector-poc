"""Hooks of zap-api-scan.py (--hook option): injection of the access token into `Authorization`.

The token is never in a command argument nor in this file: run-scans.sh gives it to the
container with `docker run -e ZAP_ACCESS_TOKEN` (no value on the command line, Docker reads
the caller's environment). Without it, the scan is anonymous and this module does nothing.

Why a renewal: the access token lasts 5 minutes, an active scan longer. A thread
exchanges the refresh token (ZAP_REFRESH_TOKEN) every 150 s for a new access
token (Keycloak, public client `collector-web`) and replaces the ZAP rule. Nothing
is displayed: the logs only contain the number of renewals.
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
CA_FILE = "/ts/rootCA.pem"  # mkcert authority, mounted by run-scans.sh
RULE = "collector-audit-bearer"
RENEW_EVERY_SECONDS = 150

_stop = threading.Event()
_stats = {"renewals": 0, "failures": 0}


def _set_token(zap: Any, access_token: str) -> None:
    """Sets (or replaces) the "Replacer" rule that fixes the Authorization header of requests."""
    # First set: the rule does not exist yet, the removal fails harmlessly.
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
    context = ssl.create_default_context(cafile=CA_FILE)  # TLS verification never disabled
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
        except Exception as error:  # noqa: BLE001 : never bring the scan down, nor display a token
            _stats["failures"] += 1
            print("[hook] token renewal failed: " + type(error).__name__, flush=True)


def zap_started(zap: Any, target: str) -> None:
    access_token = os.environ.get("ZAP_ACCESS_TOKEN")
    if not access_token:
        print("[hook] anonymous scan (no token)", flush=True)
        return
    _set_token(zap, access_token)
    print("[hook] authenticated scan: Authorization header set by ZAP", flush=True)
    refresh_token = os.environ.get("ZAP_REFRESH_TOKEN")
    if refresh_token:
        threading.Thread(target=_renew_loop, args=(zap, refresh_token), daemon=True).start()


def zap_pre_shutdown(zap: Any) -> None:
    _stop.set()
    if os.environ.get("ZAP_ACCESS_TOKEN"):
        print(
            "[hook] successful renewals: {renewals}, failures: {failures}".format(**_stats),
            flush=True,
        )
