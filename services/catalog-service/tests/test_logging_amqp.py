"""Les journaux de la bibliothèque AMQP sont rendus en JSON, comme ceux de l'application."""

import json
import logging

import pytest

from catalog.logging import configure_logging


def test_logs_de_la_connexion_amqp_en_json(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO")
    logging.getLogger("aiormq.connection").error("error when creating transport")
    logging.getLogger("aio_pika.robust_connection").debug("ignoré sous WARNING")
    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    entries = [json.loads(line) for line in lines]  # lève si une ligne n'est pas du JSON
    assert [e["event"] for e in entries] == ["error when creating transport"]
    assert entries[0]["level"] == "error"
