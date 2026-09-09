"""The Software Requirements Specification: the standalone artifact between
the intent model and the architecture. Solution-AGNOSTIC by doctrine - it says
WHAT must be verifiably true, never HOW (stack, endpoints, ciphers are
architecture/test-stage decisions). Functional and non-functional requirements
are first-class sections; every requirement traces to stakeholder needs."""
from __future__ import annotations

from pydantic import Field

from .base import ContractModel
from .interview import Assumption
from .requirements import Requirement


class SRSDocument(ContractModel):
    session_id: str
    intent_model_ref: str = Field(description="session_id of the IntentModel this SRS realizes.")
    purpose: str = Field(description="Why this system exists, in stakeholder language (from intent).")
    scope_summary: str = Field(description="The boundary: what the system will and will not do.")
    definitions: dict[str, str] = Field(
        default_factory=dict,
        description="Glossary carried from the intent model - the founder's terms, their meanings.",
    )
    functional: list[Requirement] = Field(description="Behavioral requirements (kind=functional).")
    non_functional: list[Requirement] = Field(description="Quality/constraint requirements (kind=non_functional).")
    constraints: list[str] = Field(
        default_factory=list,
        description="Design-space limits carried from intent (mandated stack, budget, deadlines).",
    )
    assumptions: list[Assumption] = Field(
        default_factory=list,
        description="Founder assertions carried from intent - validated later, never silently built.",
    )
    open_questions: list[str] = Field(
        default_factory=list,
        description="Unresolved founder questions carried from intent - never silently resolved.",
    )

    def requirements(self) -> list[Requirement]:
        """All requirements, functional first. The flat view assembly math uses."""
        return [*self.functional, *self.non_functional]

    def requirement_ids(self) -> set[str]:
        return {r.requirement_id for r in self.requirements()}
