"""Interview engine outputs: transcript + distilled intent model.

The interview is the moat and stays LLM-powered. Everything it emits is
typed here so spec-generator never re-reads raw conversation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import Field

from .base import ContractModel


class TurnRole(str, Enum):
    SYSTEM = "system"
    INTERVIEWER = "interviewer"
    FOUNDER = "founder"


class InterviewTurn(ContractModel):
    turn_index: int
    role: TurnRole
    text: str
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InterviewTranscript(ContractModel):
    session_id: str
    submission_id: str
    turns: list[InterviewTurn]
    completed: bool = Field(description="False if the founder abandoned mid-interview.")


class IntentModel(ContractModel):
    """The distilled 'what are we actually building' the spec hangs off.

    Every requirement traces back to a field here; every field names the
    transcript turns it came from. This is the root of the V-model's left arm.
    """

    session_id: str
    problem_statement: str
    target_users: list[str]
    core_value_proposition: str
    in_scope: list[str] = Field(description="Capabilities the product MUST have at the demo's fidelity bar.")
    out_of_scope: list[str] = Field(description="Explicit non-goals; silence here is how specs balloon.")
    external_integrations: list[str] = Field(
        default_factory=list, description="Web APIs / services the app consumes (allowed; app itself stays a web app)."
    )
    constraints: list[str] = Field(default_factory=list, description="Budget, compliance, platform, team constraints.")
    open_questions: list[str] = Field(
        default_factory=list,
        description="Questions the founder could not answer. Carried into the punch list, never silently resolved.",
    )
    source_turns: dict[str, list[int]] = Field(
        description="Field name -> transcript turn indexes the field was distilled from. Auditability, not decoration."
    )
