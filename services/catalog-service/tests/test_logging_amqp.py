"""The AMQP library logs are rendered as JSON, like those of the application."""

import json
import logging

import pytest

from catalog.logging import configure_logging


def test_amqp_connection_logs_as_json(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO")
    logging.getLogger("aiormq.connection").error("error when creating transport")
    logging.getLogger("aio_pika.robust_connection").debug("ignored under WARNING")
    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    entries = [json.loads(line) for line in lines]  # raises if a line is not JSON
    assert [e["event"] for e in entries] == ["error when creating transport"]
    assert entries[0]["level"] == "error"
