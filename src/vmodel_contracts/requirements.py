"""Requirements: the left arm of the V. Item-level, each one testable."""
from __future__ import annotations

from enum import Enum

from pydantic import Field

from .base import ContractModel


class Priority(str, Enum):
    MUST = "must"
    SHOULD = "should"
    COULD = "could"


class AcceptanceCriterion(ContractModel):
    """One observable, checkable statement. Written so it CAN be executed in
    the founder's own environment by the verification-loop."""

    criterion_id: str = Field(pattern=r"^AC-\d+$")
    statement: str
    executable_hint: str | None = Field(
        default=None,
        description="How verification-loop should check it: 'http GET /health returns 200', "
        "'dom contains element #cart-total', 'db row exists'. Null = human/semantic check.",
    )


class Requirement(ContractModel):
    requirement_id: str = Field(pattern=r"^R-\d+$")
    title: str
    statement: str
    priority: Priority
    acceptance: list[AcceptanceCriterion] = Field(min_length=1)
    need_ids: list[str] = Field(description="N-ids (stakeholder needs) this requirement realizes.")
    intent_fields: list[str] = Field(
        description="IntentModel fields this requirement traces to (root of the traceability chain)."
    )
    source_turns: list[int] = Field(default_factory=list)


class RequirementSet(ContractModel):
    session_id: str
    requirements: list[Requirement] = Field(min_length=1)

    def requirement_ids(self) -> set[str]:
        return {r.requirement_id for r in self.requirements}
