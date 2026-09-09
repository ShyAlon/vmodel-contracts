"""System architecture artifact: the bridge between requirements and item specs."""
from __future__ import annotations

from enum import Enum

from pydantic import Field

from .base import ContractModel


class ComponentSpec(ContractModel):
    name: str
    responsibility: str
    requirement_ids: list[str] = Field(default_factory=list)


class DecisionDriver(str, Enum):
    """ADDED 0.8.0 (ADR-0021): why the winning option won. Closed enum - a
    decision whose driver is none of these is a decision not yet understood."""

    FOUNDER_CONSTRAINT = "founder_constraint"       # the founder mandated/confined it (ADR-0019 TechPreference)
    ECOSYSTEM_MATURITY = "ecosystem_maturity"       # most mature ecosystem / library track record
    COMMUNITY_ADOPTION = "community_adoption"       # most common solution / hiring pool / docs volume
    TEAM_FIT = "team_fit"                           # what the team already knows and runs well
    SIMPLICITY = "simplicity"                       # the simplest thing that meets the requirements


class ConsideredOption(ContractModel):
    """ADDED 0.8.0 (ADR-0021): one REJECTED alternative and why it lost.
    Reasons are model judgment until retrieval grounding lands (ADR-0019
    Part 3) - rendered as unverified at the review gate."""

    option: str = Field(description="The alternative named: 'Angular', 'Vue', 'PostgreSQL'.")
    reason: str = Field(description="Why it lost - one prose sentence.")


class ArchitectureDecision(ContractModel):
    """One ADR, kept short. Rationale is load-bearing; options rejected are
    what stop the coding agent from 'improving' the architecture mid-build.

    ADR-0021 (0.8.0): every decision carries its driver and the alternatives
    it considered, so no stack pick is arbitrary. Both fields are REQUIRED-
    PRESENT: `driver` is null ONLY in pre-0.8.0 migrated artifacts (new
    producers must set a real driver - stage-enforced); `options_considered`
    may be empty (no floor - e.g. under a founder mandate, where inventing
    strawman alternatives is its own dishonesty)."""

    decision_id: str = Field(pattern=r"^ADR-\d+$")
    title: str
    decision: str
    rationale: str
    driver: DecisionDriver | None = Field(
        description="Why the winner won. Null only in legacy migrated artifacts."
    )
    options_considered: list[ConsideredOption] = Field(
        description="The leading rejected alternatives, each with why it lost. Empty is honest under a mandate."
    )
    rejected: list[str] = Field(
        default_factory=list,
        description="DEPRECATED 0.8.0 - kept so 0.7.x payloads parse; new producers leave it empty.",
    )


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

