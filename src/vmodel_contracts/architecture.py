"""System architecture artifact: the bridge between requirements and item specs."""
from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from .base import ContractModel
from .identity import normalize_identity


class ComponentSpec(ContractModel):
    name: str
    responsibility: str
    requirement_ids: list[str] = Field(default_factory=list)
    baseline_refs: list[str] = Field(
        default_factory=list,
        description="Canonical SystemBaseline refs proving where this component exists.",
    )
    migration: bool = Field(
        default=False,
        description="True when this is a new/replaced component rather than baseline-preserving work.",
    )
    migration_adr_title: str | None = Field(
        default=None,
        description="Exact title of the migration ADR authorizing this departure; null when migration is false.",
    )


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



class TechnologySelection(ContractModel):
    slot_id: str = Field(pattern=r"^slot:[a-z0-9][a-z0-9-]*$")
    technology_id: str = Field(pattern=r"^(tech|off-list):[a-z0-9][a-z0-9-]*$")
    display_name: str = Field(min_length=1)
    baseline_refs: list[str] = Field(default_factory=list)
    off_list_justification: str | None = None

    @model_validator(mode="after")
    def off_list_is_explained(self):
        if self.technology_id.startswith("off-list:") and not (self.off_list_justification or "").strip():
            raise ValueError("off-list technology requires off_list_justification")
        if not self.technology_id.startswith("off-list:") and self.off_list_justification is not None:
            raise ValueError("off_list_justification belongs only to off-list technology")
        return self

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
    baseline_refs: list[str] = Field(
        default_factory=list,
        description="Source refs from SystemBaseline supporting this decision.",
    )
    migration: bool = Field(
        default=False,
        description="True only when this decision departs from the SystemBaseline.",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Concrete evidence justifying a migration; required when migration is true.",
    )
    affected_repositories: list[str] = Field(
        default_factory=list,
        description="Baseline repository names changed by a migration; required when migration is true.",
    )
    founder_decision_refs: list[str] = Field(
        default_factory=list, description="Decided founder-register item ids supporting this ADR; source validation is stage-owned.")
    executes_concept_ids: list[str] = Field(default_factory=list)
    technology_selections: list[TechnologySelection] = Field(default_factory=list)
    rejected: list[str] = Field(
        default_factory=list,
        description="DEPRECATED 0.8.0 - kept so 0.7.x payloads parse; new producers leave it empty.",
    )


class StackEntryStatus(str, Enum):
    """A non-executable outcome for a considered architecture stack slot."""

    RESEARCH_REQUIRED = "research_required"
    NOT_APPLICABLE = "not_applicable"


class FounderStackDecision(ContractModel):
    """ADDED 0.26.0: the founder's own answer for a research_required slot."""

    text: str = Field(min_length=1, max_length=2000)
    reason: str = Field(min_length=1, max_length=1000, description="One line: why the founder chose this.")
    actor: str = Field(min_length=1, max_length=240)
    at: str = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def text_not_blank(self):
        if not self.text.strip():
            raise ValueError("founder decision text must not be blank")
        if not self.reason.strip():
            raise ValueError("founder decision reason must not be blank")
        return self


class StackEntryDisposition(ContractModel):
    """A considered stack slot that is deliberately not a technology choice.

    Delegated or ambiguous discovery is research_required. not_applicable is
    reserved for a slot that genuinely does not apply to the concept.
    """

    key: str = Field(min_length=1)
    status: StackEntryStatus
    research_brief: str | None = None
    reason: str | None = None
    candidate_options: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="ADDED 0.26.0: up to three proposed answers the founder can pick from; the founder may still write their own.",
    )
    founder_decision: FounderStackDecision | None = Field(
        default=None,
        description="ADDED 0.26.0: the founder's decision for a research_required slot; a decided slot counts as resolved.",
    )

    @model_validator(mode="after")
    def required_explanation(self):
        if self.founder_decision is not None and self.status != StackEntryStatus.RESEARCH_REQUIRED:
            raise ValueError("founder_decision belongs only to research_required")
        if self.candidate_options and self.status != StackEntryStatus.RESEARCH_REQUIRED:
            raise ValueError("candidate_options belong only to research_required")
        if any(not o.strip() for o in self.candidate_options):
            raise ValueError("candidate_options must not be blank")
        if len({o.strip().lower() for o in self.candidate_options}) != len(self.candidate_options):
            raise ValueError("candidate_options must be distinct")
        if self.status == StackEntryStatus.RESEARCH_REQUIRED:
            if not (self.research_brief or "").strip():
                raise ValueError("research_required entry requires research_brief")
            if self.reason is not None:
                raise ValueError("reason belongs only to not_applicable")
        else:
            if not (self.reason or "").strip():
                raise ValueError("not_applicable entry requires reason")
            if self.research_brief is not None:
                raise ValueError("research_brief belongs only to research_required")
        return self


class StackEntry(ContractModel):
    """ADDED 0.13.0: one technology choice with its grounding CO-LOCATED.

    Replaces the pre-0.13.0 parallel maps (`stack` + `stack_baseline_refs`),
    whose cross-map key-set invariant a constrained grammar cannot enforce -
    the 2026-09-11 phi4 live failure emitted a schema-legal `stack` map with
    a bogus `stack_baseline_refs` string key inside it, and the two maps' key
    sets disagreed. Co-locating each value with its evidence makes that
    misplacement structurally impossible: there is no second map to keep in
    sync.
    """

    key: str = Field(min_length=1, description="The technology slot named: 'language', 'database', 'model_runtime'.")
    value: str = Field(min_length=1, description="The chosen technology: 'Python 3.14', 'PostgreSQL 17'.")
    baseline_refs: list[str] = Field(
        default_factory=list,
        description="Canonical SystemBaseline refs supporting the choice; [] marks a migration choice.",
    )
    decision_id: str = Field(pattern=r"^ADR-\d+$", description="ADR that owns this projected selection.")
    technology_id: str = Field(pattern=r"^(tech|off-list):[a-z0-9][a-z0-9-]*$")
    migration_adr_id: str | None = Field(
        default=None,
        pattern=r"^ADR-\d+$",
        description="Pipeline-assigned id of the migration ADR authorizing this departure; "
                    "null unless baseline_refs is empty (a migration choice).",
    )


class ArchitectureOverview(ContractModel):
    session_id: str
    baseline_id: str | None = Field(
        default=None,
        description="Exact SystemBaseline reconciled by this architecture; null only for legacy artifacts.",
    )
    stack_entries: list[StackEntry] = Field(
        description="Named technology choices, each co-located with its SystemBaseline grounding; "
                    "never inferred from an archetype. Keys are unique."
    )
    stack_entry_dispositions: list[StackEntryDisposition] = Field(
        default_factory=list,
        description="Considered but unresolved or excluded slots. These are never executable stack choices.",
    )
    components: list[ComponentSpec]
    decisions: list[ArchitectureDecision]
    non_functionals: dict[str, str] = Field(
        default_factory=dict,
        description="Security, privacy, performance, scaling positions - each one checkable, each one traced.",
    )

    @model_validator(mode="after")
    def stack_is_adr_projection(self):
        concrete_keys = [normalize_identity(e.key) for e in self.stack_entries]
        disposition_keys = [normalize_identity(e.key) for e in self.stack_entry_dispositions]
        all_keys = concrete_keys + disposition_keys
        if len(all_keys) != len(set(all_keys)):
            raise ValueError("stack slot keys must be unique across entries and dispositions")
        selections = [(d.decision_id, x) for d in self.decisions for x in d.technology_selections]
        slot_ids = [x.slot_id for _, x in selections]
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError("technology selection slot ids must be unique across ADRs")
        projected = {(x.slot_id.removeprefix("slot:"), x.technology_id, did) for did, x in selections}
        actual = {(normalize_identity(e.key), e.technology_id, e.decision_id) for e in self.stack_entries}
        if projected != actual:
            raise ValueError("stack_entries must be the exact projection of ADR technology_selections")
        return self




def open_stack_decisions(architecture: "ArchitectureOverview") -> list[StackEntryDisposition]:
    """research_required slots the founder has not decided yet."""
    return [
        d for d in architecture.stack_entry_dispositions
        if d.status == StackEntryStatus.RESEARCH_REQUIRED and d.founder_decision is None
    ]
