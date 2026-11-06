"""Tests du profil de charge « pic »."""

from peak_profile import PeakProfile, phase, stage

PROFILE = PeakProfile(50, 1.0, 180.0, 160, 5.0, 900.0)


def test_nominal_then_peak() -> None:
    assert stage(PROFILE, 0.0, False) == (50, 1.0)
    assert stage(PROFILE, 179.9, False) == (50, 1.0)
    assert stage(PROFILE, 180.0, False) == (160, 5.0)
    assert phase(PROFILE, 179.9) == "nominal"
    assert phase(PROFILE, 180.0) == "peak"


def test_stops_on_request_or_at_the_limit() -> None:
    assert stage(PROFILE, 300.0, True) is None
    assert stage(PROFILE, 900.0, False) is None
    assert stage(PROFILE, 899.0, False) == (160, 5.0)
