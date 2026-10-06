"""Concept of Operations (CONOPS): the founder-approved operating concept.

This artifact sits between interview and needs. It records how the product is
used in the real world and, separately, the explicit concept-level choice that
downstream architecture must execute rather than reinvent.
"""
from __future__ import annotations

from pydantic import Field, model_validator

from .identity import canonical_concept_id

from .base import ContractModel


class StakeholderContext(ContractModel):
    """One stakeholder's operational setting, in founder-grounded language."""

    stakeholder: str = Field(min_length=1)
    role: str = Field(min_length=1, description="What this stakeholder does in the operation.")
    goals: list[str] = Field(min_length=1, description="Outcomes this stakeholder needs from the operation.")
    operating_environment: str = Field(
        min_length=1, description="Where/when the stakeholder operates and material surrounding conditions."
    )
    source_turns: list[int] = Field(
        min_length=1, description="Interview turns grounding this context."
    )


class OperationalScenario(ContractModel):
    """A concrete end-to-end use scenario, not a component or UI design."""

    scenario_id: str = Field(pattern=r"^OS-\d+$")
    name: str = Field(min_length=1)
    trigger: str = Field(min_length=1)
    actors: list[str] = Field(min_length=1)
    operational_flow: list[str] = Field(
        min_length=1, description="Ordered user/operational steps, before system decomposition."
    )
    success_outcome: str = Field(min_length=1)
    exceptions: list[str] = Field(
        default_factory=list, description="Operational deviations or failure situations the concept must handle."
    )
    no_exceptions_reason: str | None = Field(
        default=None,
        description="ADDED 0.24.0: why this scenario has no exceptions. Only allowed when exceptions is empty; "
        "a blank reason is invalid.",
    )
    source_turns: list[int] = Field(
        min_length=1, description="Interview turns grounding this scenario."
    )

    @model_validator(mode="after")
    def _reason_matches_exceptions(self) -> "OperationalScenario":
        if self.no_exceptions_reason is not None:
            if not self.no_exceptions_reason.strip():
                raise ValueError("no_exceptions_reason must not be blank")
            if self.exceptions:
                raise ValueError("no_exceptions_reason is only allowed when exceptions is empty")
        return self


class ConceptOption(ContractModel):
    """One product-level operating concept in the founder's comparison."""

    concept_id: str = Field(pattern=r"^concept:[a-z0-9][a-z0-9-]*$", description="Canonical concept identity; prose aliases never cross this boundary.")
    name: str = Field(min_length=1, description="Concept name, e.g. native app, PWA, web plus native bridge.")
    summary: str = Field(min_length=1)
    advantages: list[str] = Field(min_length=1)
    disadvantages: list[str] = Field(min_length=1)


class ConceptDecision(ContractModel):
    """The explicit founder decision. This is a stronger constraint than a tech preference."""

    selected_concept_id: str = Field(pattern=r"^concept:[a-z0-9][a-z0-9-]*$")
    selected_concept: str = Field(min_length=1, description="Display name of the selected concept.")
    rationale: str = Field(min_length=1, description="Why the founder selected this concept given its trade-offs.")
    founder_confirmed: bool = Field(
        description="Must be true: silence, model inference, or a provisional suggestion is not a decision."
    )
    source_turns: list[int] = Field(
        min_length=1, description="Interview turns containing the founder's explicit choice."
    )


class ConOpsDocument(ContractModel):
    """Versioned output of the CONOPS interview stage."""

    @model_validator(mode="before")
    @classmethod
    def resolve_concept_ids_at_boundary(cls, data):
        if not isinstance(data, dict):
            return data
        out = dict(data)
        options = [dict(o) for o in out.get("concept_options", [])]
        for option in options:
            option.setdefault("concept_id", canonical_concept_id(str(option.get("name", ""))))
        out["concept_options"] = options
        decision = dict(out.get("decision") or {})
        decision.setdefault("selected_concept_id", canonical_concept_id(str(decision.get("selected_concept", ""))))
        out["decision"] = decision
        return out

    session_id: str = Field(min_length=1)
    stakeholder_context: list[StakeholderContext] = Field(min_length=1)
    operational_scenarios: list[OperationalScenario] = Field(min_length=1)
    concept_options: list[ConceptOption] = Field(
        min_length=2, description="Concepts explicitly compared with advantages and disadvantages."
    )
    decision: ConceptDecision

    @model_validator(mode="after")
    def explicit_decision_selects_compared_option(self):
        names = [o.name for o in self.concept_options]
        if len({n.casefold() for n in names}) != len(names):
            raise ValueError("concept option names must be unique")
        ids = [o.concept_id for o in self.concept_options]
        if len(set(ids)) != len(ids):
            raise ValueError("concept option ids must be unique")
        selected = next((o for o in self.concept_options if o.concept_id == self.decision.selected_concept_id), None)
        if selected is None:
            raise ValueError("selected_concept_id must reference one concept_options entry")
        if self.decision.selected_concept.casefold() != selected.name.casefold():
            raise ValueError("selected_concept display name must match selected_concept_id")
        if not self.decision.founder_confirmed:
            raise ValueError("CONOPS decision must be explicitly founder-confirmed")
        scenario_ids = [s.scenario_id for s in self.operational_scenarios]
        if len(set(scenario_ids)) != len(scenario_ids):
            raise ValueError("operational scenario ids must be unique")
        return self
