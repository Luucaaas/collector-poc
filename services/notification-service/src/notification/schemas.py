"""Modèle de base des corps de requête : un champ inconnu est refusé (ENF-07)."""

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
