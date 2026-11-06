"""Profil de charge « pic » du protocole 5 : charge nominale, puis pic, jusqu'à un fichier d'arrêt.

Module pur (aucun import de Locust) : `locustfile.py` y branche une `LoadTestShape`, activée
seulement par `LOAD_PROFILE=peak`. Sans cette variable, le comportement de P8-02 est inchangé.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PeakProfile:
    nominal_users: (
        int  # charge de référence (I3), montée de `nominal_rate` utilisateurs par seconde
    )
    nominal_rate: float
    nominal_seconds: float  # durée de la phase nominale, montée comprise
    peak_users: int  # charge du pic, montée de `peak_rate` utilisateurs par seconde
    peak_rate: float
    max_seconds: float  # durée totale maximale (filet de sécurité : le script arrête avant)


def stage(profile: PeakProfile, elapsed: float, stop_requested: bool) -> tuple[int, float] | None:
    """(utilisateurs, vitesse de montée) à l'instant `elapsed`, ou None pour arrêter le test."""
    if stop_requested or elapsed >= profile.max_seconds:
        return None
    if elapsed < profile.nominal_seconds:
        return profile.nominal_users, profile.nominal_rate
    return profile.peak_users, profile.peak_rate


def phase(profile: PeakProfile, elapsed: float) -> str:
    """Nom de la phase à l'instant `elapsed` (utilisé pour dater les transitions)."""
    return "nominal" if elapsed < profile.nominal_seconds else "peak"
