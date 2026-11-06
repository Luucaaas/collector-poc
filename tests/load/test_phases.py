"""Tests de l'analyse du protocole 5 (percentiles, phases, chronologie de l'HPA), sans réseau."""

from pathlib import Path

import phases as p

HEADER = "epoch,name,response_ms,status,failed\n"


def request(
    epoch: float, ms: float = 10, status: int = 200, name: str = "GET /articles"
) -> p.Request:
    return p.Request(epoch, name, ms, status, status >= 400)


def test_percentile_nearest_rank() -> None:
    values = [float(n) for n in range(1, 101)]
    assert p.percentile(values, 0.95) == 95.0
    assert p.percentile([7.0], 0.95) == 7.0
    assert p.percentile([], 0.95) is None


def test_read_requests_skips_login_and_preparation(tmp_path: Path) -> None:
    path = tmp_path / "requetes.csv"
    path.write_text(
        HEADER
        + "100.0,GET /articles,12.5,200,0\n"
        + "101.0,[connexion] formulaire,300.0,200,0\n"
        + "102.0,[prépa] POST /shops,40.0,201,0\n"
        + "103.0,POST /articles,30.0,502,1\n"
    )
    rows = p.read_requests(path)
    assert [r.name for r in rows] == ["GET /articles", "POST /articles"]
    assert rows[1].status == 502 and rows[1].failed


def test_phase_stats_counts_5xx_and_other_failures() -> None:
    rows = [
        request(1, 10),
        request(2, 20),
        request(3, 30, 503),
        request(4, 40, 404),
        request(9, 99),  # hors fenêtre
    ]
    stats = p.phase_stats("x", rows, 0, 5)
    assert (stats.requests, stats.server_errors, stats.other_failures) == (4, 1, 1)
    assert stats.p95_all == 40
    assert stats.p95_publish is None


def test_failures_around_groups_by_second() -> None:
    rows = [request(100.2, status=502), request(100.4, status=502), request(110, status=503)]
    lines = p.failures_around(rows, 100.0, 5, 60)
    assert lines[0] == "t+0 s : 2 × GET /articles (code 502)"
    assert lines[1].startswith("t+10 s")
    assert p.failures_around(rows, 500.0, 5, 60) == []


def test_samples_join_ready_replicas_and_timeline(tmp_path: Path) -> None:
    hpa, ready = tmp_path / "hpa.tsv", tmp_path / "ready.tsv"
    desired = [2, 4, 5, 5, 5, 3, 2]
    hpa.write_text(
        "".join(
            f"{1000 + 5 * i}\tcatalog-service\t{d}\t{d}\t{90 + i}\n" for i, d in enumerate(desired)
        )
    )
    ready_counts = [2, 2, 4, 5, 5, 5, 2]
    ready.write_text(
        "".join(f"{1000.6 + 5 * i}\tcatalog-service\t{n}\n" for i, n in enumerate(ready_counts))
    )
    samples = p.read_samples(hpa, ready)
    assert samples[3].ready == 5
    timeline = p.build_timeline(
        {"nominal_start": 900.0, "peak_start": 1000.0},
        {"stop": 1020.0, "delete": 1015.0},
        samples,
    )
    assert timeline.reached[5] == 1010 and timeline.ready_at[5] == 1015
    assert timeline.reached[3] == 1005
    assert timeline.back_desired == 1030 and timeline.back_ready == 1030


def test_five_ready_event_and_pod_count_take_precedence(tmp_path: Path) -> None:
    samples = [p.Sample(1000 + 5 * i, p.CATALOG, 5, 5, 5, 80) for i in range(6)]
    pods = tmp_path / "pods.tsv"
    pods.write_text(
        "1020\tcatalog-service-a\tRunning\ttrue\t\n" * 3
        + "1025\tcatalog-service-a\tRunning\ttrue\t\n1025\tcatalog-service-b\tRunning\ttrue\t\n"
        + "1025\tnotification-service-x\tRunning\ttrue\t\n"
    )
    counts = p.read_pod_counts(pods)
    assert counts == {1020.0: 3, 1025.0: 2}
    timeline = p.build_timeline(
        {"nominal_start": 900.0, "peak_start": 1000.0},
        {"stop": 1010.0, "five_ready": 1003.4},
        samples,
        counts,
    )
    assert timeline.ready_at[5] == 1003.4
    assert timeline.back_ready == 1025.0


def test_render_reports_not_reached() -> None:
    samples = [p.Sample(1000, p.CATALOG, 3, 3, 3, 80)]
    timeline = p.build_timeline(
        {"nominal_start": 900.0, "peak_start": 1000.0}, {"stop": 1010.0}, samples
    )
    text = p.render(
        timeline,
        [request(1005)],
        samples,
        {"nominal_start": 900.0, "peak_start": 1000.0},
        (0.0, 100.0),
        "Paramètres.",
    )
    assert "HPA demande 5 réplicas | non atteint" in text
    assert "Retour à 2 réplicas : non atteint" in text
    assert "0 réponses 5xx sur 100 requêtes (0,00 %)" in text
