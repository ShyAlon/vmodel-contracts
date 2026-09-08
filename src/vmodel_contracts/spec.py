"""Item-level specs + the deliverable bundle (incl. AGENTS.md) + punch list.

The spec is the INPUT TO A CODING AGENT, not a document a founder reads.
Item-level beats mega-spec: smaller, independently verifiable, cheaper to
regenerate one item than to rerun the world.
"""
from __future__ import annotations

from enum import Enum

from pydantic import Field

from .base import ContractModel


class SpecItemKind(str, Enum):
    DATA_MODEL = "data_model"
    API_SURFACE = "api_surface"
    UI_FLOW = "ui_flow"
    BUSINESS_RULE = "business_rule"
    INTEGRATION = "integration"
    NON_FUNCTIONAL = "non_functional"   # security, privacy, performance, scaling


class ItemSpec(ContractModel):
    spec_id: str = Field(pattern=r"^SPEC-[a-z0-9-]+$")
    kind: SpecItemKind
    title: str
    body_markdown: str = Field(description="The spec itself, markdown, written for a coding agent to execute against.")
    requirement_ids: list[str] = Field(description="R-ids this item satisfies. Empty is suspicious, not forbidden.")
    depends_on: list[str] = Field(default_factory=list, description="Other SPEC-ids that must exist first.")


class PunchListItem(ContractModel):
    """One known gap, open question, or divergence a human must close.
    Traceable: always names what it blocks."""

    item_id: str = Field(pattern=r"^PL-\d+$")
    description: str
    blocks: list[str] = Field(description="Requirement or SPEC ids this gap blocks.")
    severity: str = Field(description="'blocking' | 'important' | 'nice-to-have'")


class TraceabilityEntry(ContractModel):
    """One row of the V-model traceability matrix."""

    requirement_id: str
    spec_ids: list[str]
    acceptance_criterion_ids: list[str]
    test_ids: list[str] = Field(default_factory=list, description="Filled by verification-loop.")


class SpecBundle(ContractModel):
    """The full deliverable handed to delivery-api."""

    session_id: str
    intent_model_ref: str = Field(description="session_id of the IntentModel this bundle realizes.")
    items: list[ItemSpec]
    agents_md: str = Field(description="The AGENTS.md bundle: build order, conventions, guardrails for the coding agent.")
    punch_list: list[PunchListItem]
    traceability: list[TraceabilityEntry]


class BuildMilestone(ContractModel):
    """One numbered build step, in execution order. The coding agent builds
    milestone by milestone; each milestone names the specs and tests that
    gate it."""

    order: int = Field(ge=1)
    title: str
    spec_ids: list[str]
    test_ids: list[str] = Field(default_factory=list)
    done_when: str = Field(description="Machine-checkable where possible.")


class SpecManifest(ContractModel):
    """Machine-readable index of the bundle: what exists, in what order, and
    how it traces. The verifier and the coding agent both read this first.
    Layout is Spec Kit-compatible (specs/, plan, AGENTS.md) so testers in
    that ecosystem adopt without conversion."""

    bundle_version: str
    files: dict[str, str] = Field(description="Logical name -> relative path inside the bundle.")
    milestones: list[BuildMilestone]
    target_agent: str = Field(default="claude-code", description="Demo targets one agent: Claude Code.")
