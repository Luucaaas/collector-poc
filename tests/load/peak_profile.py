"""« Peak » load profile of protocol 5: nominal load, then peak, until a stop file appears.

Pure module (no Locust import): `locustfile.py` plugs a `LoadTestShape` into it, enabled only
by `LOAD_PROFILE=peak`. Without this variable, the P8-02 behavior is unchanged.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PeakProfile:
    nominal_users: (
        int  # reference load (I3), the ramp-up speed being `nominal_rate` users per second
    )
    nominal_rate: float
    nominal_seconds: float  # duration of the nominal phase, ramp-up included
    peak_users: int  # peak load, ramped up at `peak_rate` users per second
    peak_rate: float
    max_seconds: float  # maximum total duration (safety net: the script stops before)


def stage(profile: PeakProfile, elapsed: float, stop_requested: bool) -> tuple[int, float] | None:
    """(users, ramp-up rate) at instant `elapsed`, or None to stop the test."""
    if stop_requested or elapsed >= profile.max_seconds:
        return None
    if elapsed < profile.nominal_seconds:
        return profile.nominal_users, profile.nominal_rate
    return profile.peak_users, profile.peak_rate


def phase(profile: PeakProfile, elapsed: float) -> str:
    """Name of the phase at instant `elapsed` (used to date the transitions)."""
    return "nominal" if elapsed < profile.nominal_seconds else "peak"
