"""Jeu de données de la démonstration, créé par l'API avec le vrai flux PKCE (relançable).

Lancé par `donnees-demo.sh`, qui fournit les mots de passe par l'environnement
(DEMO_<COMPTE>_PASSWORD)
et l'autorité de mkcert par REQUESTS_CA_BUNDLE. Aucun mot de passe ni jeton n'est affiché ni écrit.

Réutilise les fonctions pures de tests/load/auth.py (PKCE, formulaire de Keycloak), comme
docs/06-securite/scans/pkce_login.py : la connexion traverse ce que traverse le navigateur.

Relançable sans doublon : chaque objet est cherché avant d'être créé (catégorie par son nom,
boutique par son nom parmi celles du vendeur, article par son titre dans sa boutique).
"""

import os
import secrets
import sys
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tests" / "load"))
import auth  # noqa: E402

API = "https://api.127.0.0.1.sslip.io"
CATALOG = f"{API}/catalog/api/v1"
NOTIFICATION = f"{API}/notification/api/v1"
KEYCLOAK = "https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect"
CLIENT_ID = "collector-web"
REDIRECT_URI = "https://app.127.0.0.1.sslip.io/"
TIMEOUT = 20

CATEGORIES = [
    "Figurines",
    "Cartes à collectionner",
    "Jeux vidéo rétro",
    "Vinyles",
    "Monnaies et timbres",
]
# Catégorie suivie par chloe : celle où alice publie en direct (une notification doit arriver).
FOLLOWED = ["Figurines"]

# vendeur -> (nom de la boutique, [(titre, description, catégorie, prix, frais de port)])
SHOPS: dict[str, tuple[str, list[tuple[str, str, str, str, str]]]] = {
    "alice": (
        "Le Comptoir d'Alice",
        [
            (
                "Figurine Dark Vador Kenner 1978",
                "Figurine d'origine de la première série, cape en tissu, très bon état.",
                "Figurines",
                "85.00",
                "6.00",
            ),
            (
                "Figurine Luke Skywalker Kenner 1978",
                "Sabre laser jaune d'origine, articulations fermes, léger jaunissement.",
                "Figurines",
                "70.00",
                "6.00",
            ),
            (
                "Figurine Goldorak Popy vintage",
                "Robot en métal et plastique des années 1980, boîte d'origine abîmée.",
                "Figurines",
                "140.00",
                "9.00",
            ),
            (
                "Console Game Boy Color violette",
                "Console révisée, écran sans rayure, fonctionne parfaitement, livrée sans jeu.",
                "Jeux vidéo rétro",
                "65.00",
                "7.00",
            ),
            (
                "Jeu Zelda Ocarina of Time pour Nintendo 64",
                "Cartouche en bon état, pile de sauvegarde neuve, sans boîte.",
                "Jeux vidéo rétro",
                "48.00",
                "5.50",
            ),
        ],
    ),
    "bob": (
        "Bob Collection",
        [
            (
                "Carte Dracaufeu holographique, set de base",
                "Édition de 1999 en français, coins légèrement usés, protégée sous pochette rigide.",  # noqa: E501
                "Cartes à collectionner",
                "320.00",
                "4.00",
            ),
            (
                "Carte Magic Force of Will, édition Alliances",
                "Carte rare en anglais, état proche du neuf, jamais jouée.",
                "Cartes à collectionner",
                "95.00",
                "4.00",
            ),
            (
                "Vinyle Daft Punk Homework, édition originale",
                "Double album de 1997, pochette et disques en très bon état.",
                "Vinyles",
                "75.00",
                "8.00",
            ),
            (
                "Vinyle Pink Floyd The Wall, pressage français",
                "Pressage de 1979, pochette ouvrante avec ses encarts d'origine.",
                "Vinyles",
                "55.00",
                "8.00",
            ),
            (
                "Pièce de 2 francs Semeuse",
                "Pièce de collection en argent, belle patine, sous capsule.",
                "Monnaies et timbres",
                "12.50",
                "2.50",
            ),
            (
                "Timbre Marianne de Gandon neuf",
                "Timbre de 1945, neuf avec gomme d'origine, bien centré.",
                "Monnaies et timbres",
                "18.00",
                "2.50",
            ),
        ],
    ),
}


def password_for(user: str) -> str:
    variable = f"DEMO_{user.upper()}_PASSWORD"
    value = os.environ.get(variable)
    if not value:
        raise SystemExit(
            f"Variable d'environnement {variable} absente ou vide (voir donnees-demo.sh)."
        )
    return value


def login(user: str) -> dict[str, str]:
    """Authorization Code + PKCE S256 ; renvoie l'en-tête Authorization (jeton jamais affiché)."""
    verifier, challenge = auth.pkce_pair()
    state = secrets.token_urlsafe(16)
    http = (
        requests.Session()
    )  # un jeu de cookies par compte (pas d'authentification unique croisée)
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid profile",
        "state": state,
        "nonce": secrets.token_urlsafe(16),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    page = http.get(f"{KEYCLOAK}/auth", params=params, timeout=TIMEOUT)
    if page.status_code != 200:
        raise SystemExit(f"Connexion de {user} : page d'autorisation HTTP {page.status_code}.")
    submit = http.post(
        auth.extract_form_action(page.text),
        data={"username": user, "password": password_for(user), "credentialId": ""},
        allow_redirects=False,
        timeout=TIMEOUT,
    )
    if submit.status_code != 302:
        raise SystemExit(f"Connexion de {user} : formulaire HTTP {submit.status_code}.")
    code = auth.extract_code(submit.headers.get("Location", ""), state)
    reply = http.post(
        f"{KEYCLOAK}/token",
        data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "code": code,
            "code_verifier": verifier,
        },
        timeout=TIMEOUT,
    )
    if reply.status_code != 200:
        raise SystemExit(f"Connexion de {user} : échange du code HTTP {reply.status_code}.")
    return {"Authorization": f"Bearer {reply.json()['access_token']}"}


def call(method: str, url: str, expected: set[int], **kwargs: Any) -> requests.Response:
    reply = requests.request(method, url, timeout=TIMEOUT, **kwargs)
    if reply.status_code not in expected:
        raise SystemExit(
            f"{method} {url.replace(API, '')} : HTTP {reply.status_code} (attendu {sorted(expected)})."  # noqa: E501
        )
    return reply


def ensure_categories(admin: dict[str, str]) -> dict[str, str]:
    existing = {
        c["name"]: c["id"] for c in call("GET", f"{CATALOG}/categories", {200}).json()["items"]
    }
    created = 0
    for name in CATEGORIES:
        if name not in existing:
            reply = call("POST", f"{CATALOG}/categories", {201}, json={"name": name}, headers=admin)
            existing[name] = reply.json()["id"]
            created += 1
    print(f"Catégories : {len(CATEGORIES)} attendues, {created} créée(s).")
    return existing


def ensure_shop(headers: dict[str, str], name: str) -> str:
    shops = call("GET", f"{CATALOG}/shops/me", {200}, headers=headers).json()["items"]
    for shop in shops:
        if shop["name"] == name:
            return str(shop["id"])
    reply = call("POST", f"{CATALOG}/shops", {201}, json={"name": name}, headers=headers)
    return str(reply.json()["id"])


def ensure_articles(user: str, headers: dict[str, str], categories: dict[str, str]) -> None:
    shop_name, articles = SHOPS[user]
    shop_id = ensure_shop(headers, shop_name)
    listed = call(
        "GET", f"{CATALOG}/articles", {200}, params={"shop_id": shop_id, "limit": 100}
    ).json()["items"]
    titles = {a["title"] for a in listed}
    created = 0
    for title, description, category, price, shipping in articles:
        if title in titles:
            continue
        reply = call(
            "POST",
            f"{CATALOG}/articles",
            {201},
            headers=headers,
            json={
                "shop_id": shop_id,
                "category_id": categories[category],
                "title": title,
                "description": description,
                "photo_urls": [f"https://images.example.com/{secrets.token_hex(4)}.jpg"],
                "price": price,
                "shipping_fee": shipping,
            },
        )
        if reply.json().get("status") != "PUBLISHED":
            raise SystemExit(
                f"Article « {title} » rejeté par le contrôle : {reply.json().get('rejection_reasons')}."  # noqa: E501
            )
        created += 1
    print(f"{shop_name} ({user}) : {len(articles)} articles attendus, {created} créé(s).")


def subscribe_chloe(categories: dict[str, str]) -> None:
    """chloe suit les catégories de FOLLOWED : fait après les articles, pour que le jeu de départ
    ne lui envoie aucune notification (la démonstration en provoque en direct)."""
    headers = login("chloe")
    ids = [categories[name] for name in FOLLOWED]
    call("PUT", f"{NOTIFICATION}/me/interests", {200}, json={"category_ids": ids}, headers=headers)
    call(
        "PUT",
        f"{NOTIFICATION}/me/preferences",
        {200},
        json={"new_article": True, "price_changed": True},
        headers=headers,
    )
    print(
        f"chloe suit : {', '.join(FOLLOWED)} (préférences : nouvel article et changement de prix)."
    )


def main() -> int:
    categories = ensure_categories(login("admin"))
    for user in SHOPS:
        ensure_articles(user, login(user), categories)
    subscribe_chloe(categories)
    foreign = sorted(
        set(c["name"] for c in call("GET", f"{CATALOG}/categories", {200}).json()["items"])
        - set(CATEGORIES)
    )
    if foreign:
        print(
            f"ATTENTION : catégories hors démo présentes ({', '.join(foreign)}) : le catalogue n'est pas propre.",  # noqa: E501
            file=sys.stderr,
        )
        print(
            "Pour un catalogue propre : refaire un cluster neuf (voir script-demo.md, « La veille »).",  # noqa: E501
            file=sys.stderr,
        )
        return 3
    total = call("GET", f"{CATALOG}/articles", {200}, params={"limit": 1}).json()["total"]
    print(f"Catalogue : {total} articles publiés, {len(CATEGORIES)} catégories.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
