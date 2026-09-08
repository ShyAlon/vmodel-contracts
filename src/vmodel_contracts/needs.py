"""Stakeholder needs: the top of the V's left arm, above system requirements.
Every requirement traces to a need; every need traces to the intent model."""
from __future__ import annotations

from pydantic import Field

from .base import ContractModel
from .requirements import RequirementKind


class StakeholderNeed(ContractModel):
    need_id: str = Field(pattern=r"^N-\d+$")
    stakeholder: str = Field(description="Who holds the need: 'founder', 'end user: admin', 'integrator', ...")
    statement: str = Field(description="The need in the stakeholder's terms, not solution language.")
    kind: RequirementKind = Field(description="Functional vs non-functional; carried from the intent need.")
    intent_fields: list[str] = Field(description="IntentModel fields this need traces to.")
    intent_need_ids: list[str] = Field(
        default_factory=list, description="SN-ids (IntentModel.stakeholder_needs) this need carries forward."
    )


class StakeholderNeedsSet(ContractModel):
    session_id: str
    needs: list[StakeholderNeed] = Field(min_length=1)
