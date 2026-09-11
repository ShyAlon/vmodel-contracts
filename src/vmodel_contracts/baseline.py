"""Versioned description of the system that architecture work must preserve."""
from __future__ import annotations

from enum import Enum
from pydantic import Field, model_validator
from .base import ContractModel


class BaselineMode(str, Enum):
    EXISTING = "existing"
    GREENFIELD = "greenfield"


class RepositoryManifest(ContractModel):
    """Facts about one repository. Values are evidence, not design suggestions."""
    name: str = Field(min_length=1, pattern=r"^[A-Za-z0-9_.-]+$")
    languages: list[str] = Field(min_length=1)
    package_entry_points: list[str] = Field(default_factory=list)
    module_entry_points: list[str] = Field(default_factory=list)
    existing_artifacts: list[str] = Field(default_factory=list)
    existing_contracts: list[str] = Field(default_factory=list)
    runtime: list[str] = Field(default_factory=list)
    persistence: list[str] = Field(default_factory=list)
    integrations: list[str] = Field(default_factory=list)
    immutable_decisions: list[str] = Field(default_factory=list)


class SystemBaseline(ContractModel):
    """Architecture source of truth supplied before generation.

    `existing` describes the real system. `greenfield` explicitly states that
    no repositories or inherited decisions exist; it is never inferred from a
    missing file.
    """
    baseline_version: str = Field(default="1.0", pattern=r"^\d+\.\d+$")
    baseline_id: str = Field(min_length=1)
    system_name: str = Field(min_length=1)
    mode: BaselineMode
    repositories: list[RepositoryManifest] = Field(default_factory=list)
    immutable_decisions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def mode_matches_content(self):
        if self.mode == BaselineMode.GREENFIELD and (self.repositories or self.immutable_decisions):
            raise ValueError("greenfield baseline must declare no repositories or inherited decisions")
        if self.mode == BaselineMode.EXISTING and not self.repositories:
            raise ValueError("existing baseline requires at least one repository manifest")
        names = [r.name for r in self.repositories]
        if len(names) != len(set(names)):
            raise ValueError("repository names must be unique")
        return self
