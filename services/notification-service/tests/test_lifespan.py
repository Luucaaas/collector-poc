"""Arrêt du lifespan : fermeture garantie même en cas d'erreur (Sonar S9152)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from notification.main import create_app
from tests.conftest import build_settings


class _Fake:
    def __init__(self, calls: list[str], *, fail_on_close: bool = False) -> None:
        self.calls = calls
        self.fail_on_close = fail_on_close

    async def start(self) -> None:
        self.calls.append("start")

    async def close(self) -> None:
        self.calls.append("close")
        if self.fail_on_close:
            raise RuntimeError("fermeture en échec")


def _spy_dispose(monkeypatch: pytest.MonkeyPatch, calls: list[str]) -> None:
    async def dispose(self: AsyncEngine, close: bool = True) -> None:
        calls.append("dispose")

    monkeypatch.setattr(AsyncEngine, "dispose", dispose)


async def test_arret_normal_ferme_puis_libere_le_pool(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    _spy_dispose(monkeypatch, calls)
    app = create_app(build_settings())
    app.state.consumer = _Fake(calls)
    async with app.router.lifespan_context(app):
        pass
    assert calls == ["start", "close", "dispose"]


async def test_sortie_en_erreur_ferme_quand_meme(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    _spy_dispose(monkeypatch, calls)
    app = create_app(build_settings())
    app.state.consumer = _Fake(calls)
    with pytest.raises(RuntimeError, match="boom"):
        async with app.router.lifespan_context(app):
            raise RuntimeError("boom")
    assert calls == ["start", "close", "dispose"]


async def test_pool_libere_meme_si_la_fermeture_echoue(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    _spy_dispose(monkeypatch, calls)
    app = create_app(build_settings())
    app.state.consumer = _Fake(calls, fail_on_close=True)
    with pytest.raises(RuntimeError, match="fermeture en échec"):
        async with app.router.lifespan_context(app):
            pass
    assert calls == ["start", "close", "dispose"]
