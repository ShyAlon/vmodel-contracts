"""Requirements: the left arm of the V. Item-level, each one testable."""
from __future__ import annotations

from enum import Enum

from pydantic import Field

from .base import ContractModel


class Priority(str, Enum):
    MUST = "must"
    SHOULD = "should"
    COULD = "could"


class RequirementKind(str, Enum):
    """The classic SE split. Also classifies stakeholder NEEDS at intent time:
    a need is the kind of requirement it will become. Non-functional covers
    security, performance, privacy, usability, auditability, cost, ..."""
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"


class AcceptanceCriterion(ContractModel):
    """One observable, checkable statement. Written so it CAN be executed in
    the founder's own environment by the verification-loop."""

    criterion_id: str = Field(pattern=r"^AC-\d+$")
    statement: str
    executable_hint: str | None = Field(
        default=None,
        description="How verification-loop should check it: 'http GET /health returns 200', "
        "'ui shows the cart total', 'db row exists'. Null = human/semantic check. "
        "Authored DOWNSTREAM (test-spec stage, where the stack exists) - the SRS itself stays "
        "solution-agnostic; the criterion statement never names the implementation.",
    )


class MergedRequirement(ContractModel):
    """Provenance of an automatic near-duplicate merge: what was absorbed and why."""

    requirement_id: str = Field(pattern=r"^R-\d+$", description="The absorbed requirement's id.")
    title: str
    statement: str
    score: float = Field(description="Content-word overlap that triggered the merge.")
    rule: str = Field(default="srs.duplicate_requirement", description="The check that merged it.")


class Requirement(ContractModel):
    requirement_id: str = Field(pattern=r"^R-\d+$")
    title: str
    statement: str
    priority: Priority
    acceptance: list[AcceptanceCriterion] = Field(min_length=1)
    kind: RequirementKind = Field(description="Functional behavior vs non-functional quality/constraint on behavior.")
    need_ids: list[str] = Field(description="N-ids (stakeholder needs) this requirement realizes.")
    intent_fields: list[str] = Field(
        description="IntentModel fields this requirement traces to (root of the traceability chain)."
    )
    source_turns: list[int] = Field(default_factory=list)
    merged_from: list[MergedRequirement] = Field(
        default_factory=list,
        description="ADDED 0.23.0: requirements automatically absorbed into this one as near-duplicates, "
        "with their original wording and the score. Empty for an unmerged requirement.",
    )


class RequirementSet(ContractModel):
    session_id: str
    requirements: list[Requirement] = Field(min_length=1)

    def requirement_ids(self) -> set[str]:
        return {r.requirement_id for r in self.requirements}
