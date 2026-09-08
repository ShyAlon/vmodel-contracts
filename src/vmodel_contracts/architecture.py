"""System architecture artifact: the bridge between requirements and item specs."""
from __future__ import annotations

from pydantic import Field

from .base import ContractModel


class ComponentSpec(ContractModel):
    name: str
    responsibility: str
    requirement_ids: list[str] = Field(default_factory=list)


class ArchitectureDecision(ContractModel):
    """One ADR, kept short. Rationale is load-bearing; options rejected are
    what stop the coding agent from 'improving' the architecture mid-build."""

    decision_id: str = Field(pattern=r"^ADR-\d+$")
    title: str
    decision: str
    rationale: str
    rejected: list[str] = Field(default_factory=list, description="Options considered and why they lost.")


class ArchitectureOverview(ContractModel):
    session_id: str
    stack: dict[str, str] = Field(
        description="Named choices: framework, database, hosting, auth, ... Values are opinionated defaults from the archetype."
    )
    components: list[ComponentSpec]
    decisions: list[ArchitectureDecision]
    non_functionals: dict[str, str] = Field(
        default_factory=dict,
        description="Security, privacy, performance, scaling positions - each one checkable, each one traced.",
    )
