"""Interview engine outputs: transcript + distilled intent model.

The interview is the moat and stays LLM-powered. Everything it emits is
typed here so spec-generator never re-reads raw conversation.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum

from pydantic import Field, model_validator

from .base import ContractModel
from .requirements import RequirementKind
from .founder_register import FounderRegister


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


class IntentNeed(ContractModel):
    """One stakeholder need in the FOUNDER's language, captured at interview
    time - not a requirement yet (verifiable shall-statements are derived
    downstream, in spec-generator). The SN id is the first link of the
    traceability chain: SN -> N -> R -> SPEC -> T."""

    need_id: str = Field(pattern=r"^SN-\d+$")
    statement: str = Field(description="Founder-language need; no solution wording.")
    kind: RequirementKind = Field(description="functional behavior vs non-functional quality (security, performance, privacy, ...).")
    source_turns: list[int] = Field(default_factory=list, description="Transcript turns this need came from.")
    deferred: bool = Field(
        default=False,
        description="True when the founder said this need is for later (a future commitment, not part of "
        "this build). Set from the founder's wording, never inferred downstream. Additive; default False.",
    )
    amendment_id: str | None = Field(
        default=None,
        pattern=r"^AM-\d+$",
        description="Set when the need was added by a founder amendment after the interview "
        "(IntentModel.amendments). Such a need may have empty source_turns: its provenance is the amendment.",
    )


class FounderAmendment(ContractModel):
    """A decision the founder made OUTSIDE the interview transcript (for example in a
    review channel). Recorded with its source so renderers can show where it came from;
    it never rewrites transcript turns."""

    amendment_id: str = Field(pattern=r"^AM-\d+$")
    statement: str = Field(min_length=1)
    source: str = Field(default="founder-channel", description="Where the founder said it.")
    decided_on: date
    rationale: str = ""


class Assumption(ContractModel):
    """Something the founder ASSERTED without evidence, captured - never built.
    source_turns is load-bearing: an assumption that cannot be pointed at in
    THIS session's transcript is a fabrication and must be dropped (run-3
    defect: prompt-example echoes surfaced as founder assertions)."""

    statement: str = Field(description="The assertion, short, founder-flavored.")
    source_turns: list[int] = Field(
        min_length=1, description="Transcript turn indexes where the founder actually asserted this."
    )


class ScopeExclusion(ContractModel):
    """One out-of-scope item WITH provenance. explicit=True: the founder said
    'not this' in the transcript. explicit=False: inferred candidate - must be
    rendered AS a candidate for confirmation, never as settled boundary."""

    item: str = Field(description="The exclusion.")
    source_turns: list[int] = Field(
        default_factory=list, description="Transcript turns backing it; empty only for clearly-labeled candidates."
    )
    explicit: bool = Field(description="True only if the founder explicitly excluded this in the conversation.")


class TechArea(str, Enum):
    """Where a technology preference applies."""

    LANGUAGE = "language"
    FRAMEWORK = "framework"
    CLOUD = "cloud"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"


class TechStrength(str, Enum):
    """required binds the architecture stage; preferred guides it. 'Mentioned
    but not forced' (ADR-0019): cloud affinity is preferred unless the founder
    explicitly mandated it."""

    REQUIRED = "required"
    PREFERRED = "preferred"


class TechPreference(ContractModel):
    """A founder-STATED technology/ecosystem preference (ADR-0019). A constraint
    on design space, never solution language: it confines the architecture
    stage and must not leak into the SRS. Verified mechanically at distillation:
    source_turns required (ungrounded = dropped), unrecognized ecosystem names
    kept but warned for the approval gate."""

    area: TechArea
    preference: str = Field(description="The founder's words: 'python', 'node', 'agnostic', 'AWS', 'no cloud'.")
    strength: TechStrength = Field(
        description="required ONLY when the founder mandated it ('must be', 'locked into'); otherwise preferred."
    )
    source_turns: list[int] = Field(
        min_length=1, description="Transcript turns where the founder stated this. Empty = invented: rejected."
    )


class ResearchBrief(ContractModel):
    """Founder-delegated discovery to resolve from current sources at the architecture gate."""

    topic: str = Field(min_length=1)
    brief: str = Field(min_length=1)
    source_turns: list[int] = Field(min_length=1)


class IntentModel(ContractModel):
    """The distilled 'what are we actually building' the spec hangs off.

    Every requirement traces back to a field here; every field names the
    transcript turns it came from. This is the root of the V-model's left arm.
    """

    session_id: str
    problem_statement: str
    target_users: list[str]
    core_value_proposition: str
    stakeholder_needs: list[IntentNeed] = Field(
        min_length=1,
        description="What stakeholders NEED, split functional/non-functional. Distinct from scope "
        "(the boundary of what the system does) and from requirements (derived, verifiable - downstream).",
    )
    in_scope: list[str] = Field(description="Scope boundary: capabilities the product MUST have at the demo's fidelity bar.")
    out_of_scope: list[str] = Field(description="Explicit non-goals; silence here is how specs balloon.")
    external_integrations: list[str] = Field(
        default_factory=list, description="Web APIs / services the app consumes (allowed; app itself stays a web app)."
    )
    constraints: list[str] = Field(default_factory=list, description="Budget, compliance, platform, team constraints.")
    assumptions: list[str] = Field(
        default_factory=list,
        description="DEPRECATED since 0.4.0 - use assumption_items (grounded, per-item source_turns). "
        "Kept so 0.3.x payloads still parse; new producers leave it empty.",
    )
    assumption_items: list[Assumption] = Field(
        default_factory=list,
        description="Founder assertions without evidence, each grounded in transcript turns. "
        "Validated later, never built as needs.",
    )
    scope_exclusions: list[ScopeExclusion] = Field(
        default_factory=list,
        description="Out-of-scope WITH provenance (explicit vs inferred candidate). "
        "out_of_scope stays the flat rendered list; this is the auditable form.",
    )
    done_criteria: list[str] = Field(
        default_factory=list,
        description="Founder's acceptance conditions ('I'll know it works when...'). Not needs - "
        "they feed validation downstream. Turns tracked in source_turns['done_criteria'].",
    )
    tech_preferences: list[TechPreference] = Field(
        default_factory=list,
        description="ADDED 0.7.0 (ADR-0019): founder-stated ecosystem/cloud preferences. Constraints on "
        "design space - they confine the architecture stage, never the SRS. 'Agnostic' is recorded, "
        "not treated as silence.",
    )
    glossary: dict[str, str] = Field(
        default_factory=dict,
        description="Founder's domain terms mapped to the meaning AS THE FOUNDER USED them "
        "('exceptions' = plan deviations, 'facilities' = warehouses + stores). Keeps language "
        "consistent downstream; never invent terms the founder did not say.",
    )
    operational_concepts: list[str] = Field(
        default_factory=list,
        description="Operational/support processes the founder described (e.g. 'support team handles "
        "failures'). Not system requirements - captured so they are not lost or misclassified as NFRs.",
    )
    research_briefs: list[ResearchBrief] = Field(
        default_factory=list,
        description="Delegated engineering or external-fact discovery. Resolve from grounded sources, never model memory.",
    )
    open_questions: list[str] = Field(
        default_factory=list,
        description="Questions the founder could not answer. Carried into the punch list, never silently resolved.",
    )
    amendments: list[FounderAmendment] = Field(
        default_factory=list,
        description="Founder decisions made after the interview, each with an AM-n id and its source. "
        "Additive; old payloads parse with an empty list.",
    )
    founder_register: FounderRegister | None = None
    source_turns: dict[str, list[int]] = Field(
        description="Field name -> transcript turn indexes the field was distilled from. Auditability, not decoration."
    )

    @model_validator(mode="after")
    def _amendment_refs_resolve(self) -> "IntentModel":
        ids = [a.amendment_id for a in self.amendments]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        if dup:
            raise ValueError(f"duplicate amendment ids: {dup}")
        missing = sorted({n.amendment_id for n in self.stakeholder_needs
                          if n.amendment_id and n.amendment_id not in set(ids)})
        if missing:
            raise ValueError(f"needs cite unknown amendment ids: {missing}")
        return self
