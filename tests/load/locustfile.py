"""Scénarios Locust de Collector.shop : lecteurs anonymes et vendeurs connectés.

Lancé par `run.sh` (qui fournit les mots de passe par l'environnement). Voir README.md.

Deux types d'utilisateurs, dans la proportion de 8 à 2 (80 % de lecteurs) :
- `ReaderUser` : un visiteur anonyme qui parcourt le catalogue ;
- `SellerUser` : alice ou bob, à tour de rôle, qui publie des articles et change leurs prix.

Au démarrage (`test_start`), une préparation crée la catégorie propre à l'exécution et abonne
chloe à cette catégorie : chaque publication et chaque changement de prix crée donc une
notification, ce qui alimente la métrique `notification_delay_seconds` (ENF-14).
"""

import itertools
import json
import os
import random
import threading
import time
from pathlib import Path
from typing import Any

from locust import HttpUser, TaskSet, between, events, task  # noqa: F401
from locust.clients import HttpSession, ResponseContextManager
from locust.env import Environment

import config
from interests import interests_for_run
from session import TokenHolder, login

PREPARATION = "[prépa]"
RUN_ID = os.environ.get("LOAD_RUN_ID") or time.strftime("%Y%m%d-%H%M")
RESULTS_DIR = os.environ.get("LOAD_RESULTS_DIR")


class RunState:
    """Données partagées par tous les utilisateurs d'une exécution (un seul processus Locust)."""

    category_id: str = ""
    category_name: str = ""
    plateau_start: float | None = None
    shops: dict[str, str] = {}
    # Locust rend threading coopératif (gevent) : ce verrou ne bloque pas les autres utilisateurs.
    shop_lock = threading.Lock()
    article_numbers = itertools.count(1)
    seller_numbers = itertools.count()


SELLERS = ("alice", "bob")


def record(response: ResponseContextManager, expected: set[int]) -> None:
    """Marque la réponse réussie si son code est attendu, sinon échec nommé par la nature du code.

    « HTTP 5xx » est la formule que lit `thresholds.count_5xx` pour le taux d'erreur serveur.
    Un 201 `REJECTED` est un succès métier (le contrôle automatique a fait son travail).
    """
    code = response.status_code
    if code in expected:
        response.success()  # type: ignore[no-untyped-call]
    elif code >= 500:
        response.failure(f"HTTP 5xx : {code}")  # type: ignore[no-untyped-call]
    elif code == 0:
        response.failure("erreur de connexion")  # type: ignore[no-untyped-call]
    else:
        response.failure(f"HTTP {code} inattendu")  # type: ignore[no-untyped-call]


def _write_window(update: dict[str, Any]) -> None:
    if not RESULTS_DIR:
        return
    path = Path(RESULTS_DIR) / "fenetre.json"
    data: dict[str, Any] = json.loads(path.read_text()) if path.exists() else {}
    data.update(update)
    path.write_text(json.dumps(data, indent=2))


def prepare_run(environment: Environment, **_: Any) -> None:
    """Préparation de l'exécution ; un échec l'arrête (mesurer sans elle n'aurait pas de sens)."""
    try:
        _prepare(environment)
    except Exception as error:
        print(f"Préparation impossible : {error}", flush=True)
        environment.process_exit_code = 1
        if environment.runner is not None:
            environment.runner.quit()


def _prepare(environment: Environment) -> None:
    """Catégorie de l'exécution (admin) et abonnement de chloe à cette catégorie."""
    base = environment.host or config.API_HOST

    def new_client() -> HttpSession:
        # Un client (donc un jeu de cookies) par compte : avec le cookie de session de Keycloak
        # d'admin, la connexion de chloe sauterait le formulaire (authentification unique).
        client = HttpSession(base_url=base, request_event=environment.events.request, user=None)
        client.verify = config.ca_bundle()  # vérification TLS toujours active
        return client

    client = new_client()
    admin = login(client, "admin", config.password_for("admin"))
    RunState.category_name = f"Charge {RUN_ID}"
    reply = client.post(
        f"{config.CATALOG}/categories",
        json={"name": RunState.category_name},
        headers={"Authorization": f"Bearer {admin.access_token}"},
        name=f"{PREPARATION} POST /categories",
    )
    if reply.status_code != 201:
        raise RuntimeError(f"Création de la catégorie : HTTP {reply.status_code}")
    RunState.category_id = reply.json()["id"]

    client = new_client()
    chloe = login(client, "chloe", config.password_for("chloe"))
    headers = {"Authorization": f"Bearer {chloe.access_token}"}
    current = client.get(
        f"{config.NOTIFICATION}/me/interests",
        headers=headers,
        name=f"{PREPARATION} GET /me/interests",
    )
    if current.status_code != 200:
        raise RuntimeError(f"Lecture des centres d'intérêt : HTTP {current.status_code}")
    # Les catégories « Charge … » des exécutions précédentes sont retirées (limite métier de 20),
    # toutes les autres sont gardées, puis celle de l'exécution est ajoutée.
    catalog = client.get(f"{config.CATALOG}/categories", name=f"{PREPARATION} GET /categories")
    if catalog.status_code != 200:
        raise RuntimeError(f"Lecture des catégories : HTTP {catalog.status_code}")
    interests = interests_for_run(
        current.json()["category_ids"], catalog.json()["items"], RunState.category_id
    )
    updated = client.put(
        f"{config.NOTIFICATION}/me/interests",
        json={"category_ids": interests},
        headers=headers,
        name=f"{PREPARATION} PUT /me/interests",
    )
    if updated.status_code != 200:
        raise RuntimeError(f"Mise à jour des centres d'intérêt : HTTP {updated.status_code}.")
    preferences = client.put(
        f"{config.NOTIFICATION}/me/preferences",
        json={"new_article": True, "price_changed": True},
        headers=headers,
        name=f"{PREPARATION} PUT /me/preferences",
    )
    if preferences.status_code != 200:
        raise RuntimeError(f"Mise à jour des préférences : HTTP {preferences.status_code}")


def plateau_reached(**_: Any) -> None:
    """Début du plateau : les statistiques sont remises à zéro (--reset-stats), la fenêtre aussi."""
    RunState.plateau_start = time.time()
    _write_window({"plateau_start": RunState.plateau_start, "category": RunState.category_name})


def run_finished(**_: Any) -> None:
    _write_window({"end": time.time()})


class ReaderUser(HttpUser):
    """Visiteur anonyme. Attente de 1 à 3 s entre deux actions : le temps de regarder une page de
    résultats avant de cliquer, rythme d'un parcours de catalogue (20 requêtes par seconde pour
    40 lecteurs, bien au-delà d'un trafic de démonstration)."""

    host = config.API_HOST
    weight = 8
    wait_time = between(1, 3)

    def on_start(self) -> None:
        self.client.verify = config.ca_bundle()  # vérification TLS toujours active
        self.known_ids: list[str] = []

    @task(5)
    def list_articles(self) -> None:
        params: dict[str, Any] = {"limit": 20, "offset": random.choice([0, 0, 20, 40])}
        if random.random() < 0.5 and RunState.category_id:
            params["category_id"] = RunState.category_id
        with self.client.get(
            f"{config.CATALOG}/articles", params=params, name="GET /articles", catch_response=True
        ) as response:
            record(response, {200})
            if response.status_code == 200:
                ids = [item["id"] for item in response.json().get("items", [])]
                self.known_ids = ids or self.known_ids

    @task(2)
    def list_categories(self) -> None:
        with self.client.get(
            f"{config.CATALOG}/categories", name="GET /categories", catch_response=True
        ) as response:
            record(response, {200})

    @task(3)
    def article_detail(self) -> None:
        if not self.known_ids:
            self.list_articles()
            return
        with self.client.get(
            f"{config.CATALOG}/articles/{random.choice(self.known_ids)}",
            name="GET /articles/{id}",
            catch_response=True,
        ) as response:
            record(response, {200})


class SellerUser(HttpUser):
    """Vendeur connecté (alice ou bob). Attente de 4 à 10 s : saisir une annonce ou un nouveau
    prix prend plus de temps que de lire une page. 10 vendeurs publient donc environ 1,4 fois par
    seconde, et chaque article valide déclenche une notification pour chloe."""

    host = config.API_HOST
    weight = 2
    wait_time = between(4, 10)

    def on_start(self) -> None:
        self.client.verify = config.ca_bundle()  # vérification TLS toujours active
        self.username = SELLERS[next(RunState.seller_numbers) % len(SELLERS)]
        self.tokens = TokenHolder(self.client, self.username)
        self.shop_id = self._ensure_shop()
        self.prices: dict[str, str] = {}  # articles publiés par cet utilisateur : id -> prix

    def _ensure_shop(self) -> str:
        """Une boutique par vendeur et par exécution, créée par le premier de ses utilisateurs."""
        with RunState.shop_lock:
            if self.username not in RunState.shops:
                reply = self.client.post(
                    f"{config.CATALOG}/shops",
                    json={"name": f"Boutique charge {RUN_ID} {self.username}"},
                    headers=self.tokens.headers(),
                    name=f"{PREPARATION} POST /shops",
                )
                if reply.status_code != 201:
                    raise RuntimeError(f"Création de la boutique : HTTP {reply.status_code}")
                RunState.shops[self.username] = reply.json()["id"]
            return RunState.shops[self.username]

    def _publish(self, rejected: bool) -> None:
        number = next(RunState.article_numbers)
        description = (
            "Contactez-moi directement au 06 12 34 56 78 pour conclure la vente."
            if rejected
            else "Article de démonstration du test de charge, complet et en très bon état."
        )
        price = f"{random.randint(5, 900)}.{random.randint(0, 99):02d}"
        body = {
            "shop_id": self.shop_id,
            "category_id": RunState.category_id,
            "title": f"Figurine de charge {number}",
            "description": description,
            "photo_urls": [f"https://images.example.com/charge-{number}.jpg"],
            "price": price,
            "shipping_fee": "4.90",
        }
        # Même nom pour les deux cas : la publication, contrôle automatique compris, est une seule
        # opération pour l'utilisateur (201 PUBLISHED ou 201 REJECTED).
        with self.client.post(
            f"{config.CATALOG}/articles",
            json=body,
            headers=self.tokens.headers(),
            name="POST /articles",
            catch_response=True,
        ) as response:
            record(response, {201})
            if response.status_code == 201:
                article = response.json()
                if article.get("status") == "PUBLISHED":
                    self.prices[article["id"]] = article["price"]

    @task(6)
    def publish_valid(self) -> None:
        self._publish(rejected=False)

    @task(1)
    def publish_rejected(self) -> None:
        self._publish(rejected=True)

    @task(4)
    def change_price(self) -> None:
        if not self.prices:
            self._publish(rejected=False)
            return
        article_id = random.choice(list(self.prices))
        new_price = self.prices[article_id]
        while new_price == self.prices[article_id]:
            new_price = f"{random.randint(5, 900)}.{random.randint(0, 99):02d}"
        with self.client.put(
            f"{config.CATALOG}/articles/{article_id}/price",
            json={"price": new_price},
            headers=self.tokens.headers(),
            name="PUT /articles/{id}/price",
            catch_response=True,
        ) as response:
            record(response, {200})
            if response.status_code == 200:
                self.prices[article_id] = new_price


# Enregistrement des écouteurs (plutôt que des décorateurs, que mypy juge non typés).
events.test_start.add_listener(prepare_run)  # type: ignore[no-untyped-call]
events.spawning_complete.add_listener(plateau_reached)  # type: ignore[no-untyped-call]
events.test_stop.add_listener(run_finished)  # type: ignore[no-untyped-call]
