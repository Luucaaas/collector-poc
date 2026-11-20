"""Base model of the request bodies: an unknown field is rejected (ENF-07)."""

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
