"""Collector.shop Locust scenarios: anonymous readers and logged-in sellers.

Started by `run.sh` (which provides the passwords through the environment). See README.md.

Two kinds of users, in the ratio 8 to 2 (80 % readers):
- `ReaderUser`: an anonymous visitor browsing the catalogue;
- `SellerUser`: alice or bob, in turn, who publishes articles and changes their prices.

At startup (`test_start`), a preparation creates the run's own category and subscribes chloe
to it: every publication and every price change therefore creates a notification, which
feeds the `notification_delay_seconds` metric (ENF-14).
"""

import itertools
import json
import os
import random
import threading
import time
from pathlib import Path
from typing import Any

from locust import HttpUser, LoadTestShape, TaskSet, between, events, task  # noqa: F401
from locust.clients import HttpSession, ResponseContextManager
from locust.env import Environment

import config
import peak_profile as load_profile
from interests import interests_for_run
from session import TokenHolder, login

PREPARATION = "[prépa]"
RUN_ID = os.environ.get("LOAD_RUN_ID") or time.strftime("%Y%m%d-%H%M")
RESULTS_DIR = os.environ.get("LOAD_RESULTS_DIR")


REQUEST_LOG = os.environ.get("LOAD_REQUEST_LOG")  # protocol 5: one line per request (optional)
STOP_FILE = os.environ.get("LOAD_STOP_FILE")  # protocol 5: creating it stops the test
PEAK_PROFILE = (
    load_profile.PeakProfile(
        nominal_users=int(os.environ.get("LOAD_NOMINAL_USERS", "50")),
        nominal_rate=float(os.environ.get("LOAD_NOMINAL_RATE", "1")),
        nominal_seconds=float(os.environ.get("LOAD_NOMINAL_SECONDS", "180")),
        peak_users=int(os.environ.get("LOAD_PEAK_USERS", "150")),
        peak_rate=float(os.environ.get("LOAD_PEAK_RATE", "5")),
        max_seconds=float(os.environ.get("LOAD_MAX_SECONDS", "1800")),
    )
    if os.environ.get("LOAD_PROFILE") == "peak"
    else None
)


class RunState:
    """Data shared by all the users of a run (a single Locust process)."""

    category_id: str = ""
    category_name: str = ""
    plateau_start: float | None = None
    shops: dict[str, str] = {}
    # Locust makes threading cooperative (gevent): this lock does not block the other users.
    shop_lock = threading.Lock()
    article_numbers = itertools.count(1)
    seller_numbers = itertools.count()


SELLERS = ("alice", "bob")


def record(response: ResponseContextManager, expected: set[int]) -> None:
    """Marks the response successful if its code is expected, otherwise a failure named by its kind.

    « HTTP 5xx » is the wording read by `thresholds.count_5xx` for the server error rate.
    A 201 `REJECTED` is a business success (the automatic check did its job).
    """
    code = response.status_code
    if code in expected:
        response.success()  # type: ignore[no-untyped-call]
    elif code >= 500:
        response.failure(f"HTTP 5xx : {code}")  # type: ignore[no-untyped-call]
    elif code == 0:
        response.failure("connection error")  # type: ignore[no-untyped-call]
    else:
        response.failure(f"HTTP {code} unexpected")  # type: ignore[no-untyped-call]


def _write_window(update: dict[str, Any]) -> None:
    if not RESULTS_DIR:
        return
    path = Path(RESULTS_DIR) / "fenetre.json"
    data: dict[str, Any] = json.loads(path.read_text()) if path.exists() else {}
    data.update(update)
    path.write_text(json.dumps(data, indent=2))


def prepare_run(environment: Environment, **_: Any) -> None:
    """Run preparation; a failure stops it (measuring without it would make no sense)."""
    try:
        _prepare(environment)
    except Exception as error:
        print(f"Preparation failed: {error}", flush=True)
        environment.process_exit_code = 1
        if environment.runner is not None:
            environment.runner.quit()


def _prepare(environment: Environment) -> None:
    """Run category (admin) and subscription of chloe to this category."""
    base = environment.host or config.API_HOST

    def new_client() -> HttpSession:
        # One client (hence one cookie jar) per account: with admin's Keycloak session cookie,
        # chloe's login would skip the form (single sign-on).
        client = HttpSession(base_url=base, request_event=environment.events.request, user=None)
        client.verify = config.ca_bundle()  # TLS verification always on
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
        raise RuntimeError(f"Category creation: HTTP {reply.status_code}")
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
        raise RuntimeError(f"Reading interests: HTTP {current.status_code}")
    # The « Charge … » categories of previous runs are removed (business limit of 20), all the
    # others are kept, then the one of this run is added.
    catalog = client.get(f"{config.CATALOG}/categories", name=f"{PREPARATION} GET /categories")
    if catalog.status_code != 200:
        raise RuntimeError(f"Reading categories: HTTP {catalog.status_code}")
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
        raise RuntimeError(f"Updating interests: HTTP {updated.status_code}.")
    preferences = client.put(
        f"{config.NOTIFICATION}/me/preferences",
        json={"new_article": True, "price_changed": True},
        headers=headers,
        name=f"{PREPARATION} PUT /me/preferences",
    )
    if preferences.status_code != 200:
        raise RuntimeError(f"Updating preferences: HTTP {preferences.status_code}")


def plateau_reached(**_: Any) -> None:
    """Start of the plateau: statistics are reset (--reset-stats), and so is the window."""
    RunState.plateau_start = time.time()
    _write_window({"plateau_start": RunState.plateau_start, "category": RunState.category_name})


def run_finished(**_: Any) -> None:
    _write_window({"end": time.time()})


class ReaderUser(HttpUser):
    """Anonymous visitor. Wait of 1 to 3 s between two actions: time to look at a results page
    before clicking, the pace of a catalogue visit (20 requests per second for 40 readers,
    well beyond demo traffic)."""

    host = config.API_HOST
    weight = 8
    wait_time = between(1, 3)

    def on_start(self) -> None:
        self.client.verify = config.ca_bundle()  # TLS verification always on
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
    """Logged-in seller (alice or bob). Wait of 4 to 10 s: typing a listing or a new price takes
    longer than reading a page. 10 sellers therefore publish about 1.4 times per second, and
    every valid article triggers a notification for chloe."""

    host = config.API_HOST
    weight = 2
    wait_time = between(4, 10)

    def on_start(self) -> None:
        self.client.verify = config.ca_bundle()  # TLS verification always on
        self.username = SELLERS[next(RunState.seller_numbers) % len(SELLERS)]
        self.tokens = TokenHolder(self.client, self.username)
        self.shop_id = self._ensure_shop()
        self.prices: dict[str, str] = {}  # articles published by this user: id -> price

    def _ensure_shop(self) -> str:
        """One shop per seller and per run, created by the first of its users."""
        with RunState.shop_lock:
            if self.username not in RunState.shops:
                reply = self.client.post(
                    f"{config.CATALOG}/shops",
                    json={"name": f"Boutique charge {RUN_ID} {self.username}"},
                    headers=self.tokens.headers(),
                    name=f"{PREPARATION} POST /shops",
                )
                if reply.status_code != 201:
                    raise RuntimeError(f"Shop creation: HTTP {reply.status_code}")
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
        # Same name for both cases: publication, automatic check included, is a single operation
        # for the user (201 PUBLISHED or 201 REJECTED).
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


# Listener registration (rather than decorators, which mypy considers untyped).
events.test_start.add_listener(prepare_run)  # type: ignore[no-untyped-call]
events.spawning_complete.add_listener(plateau_reached)  # type: ignore[no-untyped-call]
events.test_stop.add_listener(run_finished)  # type: ignore[no-untyped-call]


if REQUEST_LOG:
    _request_log = open(REQUEST_LOG, "w", buffering=1, encoding="utf-8")  # noqa: SIM115
    _request_log.write("epoch,name,response_ms,status,failed\n")

    def log_request(
        name: str,
        response_time: float,
        response: Any = None,
        exception: Any = None,
        start_time: float | None = None,
        **_: Any,
    ) -> None:
        """One line per request (instant, name, duration, HTTP code, failure): protocol 5 computes
        its p95 and 5xx per phase from this file, which Locust's history (10 s sliding
        window) does not allow."""
        status = getattr(response, "status_code", 0) or 0
        stamp = start_time if start_time is not None else time.time()
        label = name.replace(",", " ")
        failed = int(exception is not None)
        _request_log.write(f"{stamp:.3f},{label},{response_time:.1f},{status},{failed}\n")

    events.request.add_listener(log_request)  # type: ignore[no-untyped-call]


if PEAK_PROFILE is not None:

    class PeakShape(LoadTestShape):
        """Nominal load then peak (`profile.py`); transitions are dated in `fenetre.json`,
        the test stops when `run.sh` creates the stop file."""

        started: float | None = None
        current = ""

        def tick(self) -> tuple[int, float] | None:
            assert PEAK_PROFILE is not None
            now = time.time()
            if self.started is None:
                self.started = now
            elapsed = now - self.started
            name = load_profile.phase(PEAK_PROFILE, elapsed)
            if name != self.current:
                self.current = name
                update: dict[str, Any] = {f"{name}_start": now}
                if name == "nominal":
                    update["nominal_ramp"] = PEAK_PROFILE.nominal_users / PEAK_PROFILE.nominal_rate
                _write_window(update)
            stop = bool(STOP_FILE) and Path(str(STOP_FILE)).exists()
            return load_profile.stage(PEAK_PROFILE, elapsed, stop)
