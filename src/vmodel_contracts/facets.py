"""Immutable structured-interview schemas and evidence contracts.

Facet definitions are code-reviewed contracts. Runtime systems pin a schema
version and may record evidence or promotion proposals, but cannot mutate the
schema used by a live session.
"""
from __future__ import annotations

from enum import IntEnum
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from .base import ContractModel


EXTERNAL_OPTION_ID = 999
COVERAGE_SCHEMA_ID = "interview.coverage"
COVERAGE_SCHEMA_VERSION = "1.0.0"


class FacetValueKind(IntEnum):
    ENUM = 10
    MULTI_ENUM = 20
    NUMBER = 30
    TEXT = 40


class EvidenceDisposition(IntEnum):
    CLASSIFIED = 10
    EXTERNAL = 20
    DEAD_LETTER = 30


class DeadLetterReason(IntEnum):
    NO_MATCH = 10
    LOW_CONFIDENCE = 20
    CONFLICTING_MATCHES = 30
    PROVIDER_ERROR = 40
    UNSOLICITED_FACET = 50


class PromotionStatus(IntEnum):
    PROPOSED = 10
    ACCEPTED = 20
    REJECTED = 30
    RELEASED = 40


class FacetOption(ContractModel):
    option_id: int = Field(ge=1)
    key: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    label: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    anchors: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)


class FacetDefinition(ContractModel):
    facet_id: int = Field(ge=1)
    key: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    label: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    value_kind: FacetValueKind = FacetValueKind.ENUM
    options: list[FacetOption]

    @model_validator(mode="after")
    def require_external_and_unique_ids(self):
        ids = [item.option_id for item in self.options]
        keys = [item.key for item in self.options]
        if len(ids) != len(set(ids)) or len(keys) != len(set(keys)):
            raise ValueError("facet option ids and keys must be unique")
        if not any(item.option_id == EXTERNAL_OPTION_ID and item.key == "external" for item in self.options):
            raise ValueError("every bounded facet requires the External option")
        return self


class FacetSchema(ContractModel):
    schema_id: str = Field(min_length=1)
    schema_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    facets: list[FacetDefinition]

    @model_validator(mode="after")
    def unique_facets(self):
        ids = [item.facet_id for item in self.facets]
        keys = [item.key for item in self.facets]
        if len(ids) != len(set(ids)) or len(keys) != len(set(keys)):
            raise ValueError("facet ids and keys must be unique")
        return self


class SessionSchemaBinding(ContractModel):
    session_id: str = Field(min_length=1)
    schema_id: str = Field(min_length=1)
    schema_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")


class EvidenceRecord(ContractModel):
    evidence_id: UUID
    run_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    schema_id: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    facet_key: str | None = None
    option_id: int | None = None
    disposition: EvidenceDisposition
    raw_text: str = Field(min_length=1)
    extracted_value: Any | None = None
    provider: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    occurred_at: str = Field(min_length=1)


class DeadLetterEntry(ContractModel):
    dlq_id: UUID
    evidence_id: UUID
    run_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    schema_id: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    reason: DeadLetterReason
    raw_text: str = Field(min_length=1)
    proposed_facet_key: str | None = None
    proposed_option_key: str | None = None
    created_at: str = Field(min_length=1)


class PromotionReview(ContractModel):
    proposal_id: UUID
    source_dlq_ids: list[UUID] = Field(min_length=1)
    status: PromotionStatus
    target_schema_id: str = Field(min_length=1)
    target_schema_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    reviewer_id: str | None = None
    rationale: str | None = None
    reviewed_at: str | None = None

    @model_validator(mode="after")
    def released_requires_review(self):
        if self.status in (PromotionStatus.ACCEPTED, PromotionStatus.REJECTED, PromotionStatus.RELEASED):
            if not self.reviewer_id or not self.rationale or not self.reviewed_at:
                raise ValueError("reviewed promotions require reviewer, rationale, and timestamp")
        return self


def _external() -> FacetOption:
    return FacetOption(option_id=EXTERNAL_OPTION_ID, key="external", label="External",
        definition="Evidence does not fit a released option; preserve it without changing this schema.")


def _coverage_facet(facet_id: int, key: str, label: str, definition: str) -> FacetDefinition:
    return FacetDefinition(facet_id=facet_id, key=key, label=label, definition=definition, options=[
        FacetOption(option_id=10, key="uncovered", label="Uncovered", definition="No usable evidence recorded."),
        FacetOption(option_id=20, key="thin", label="Thin", definition="Some evidence exists but the closure rule is not met."),
        FacetOption(option_id=30, key="covered", label="Covered", definition="Concrete evidence meets the closure rule."),
        FacetOption(option_id=40, key="skipped", label="Skipped", definition="Founder explicitly chose not to answer."),
        FacetOption(option_id=50, key="delegated", label="Delegated", definition="Founder explicitly delegated the decision."),
        _external(),
    ])


COVERAGE_SCHEMA = FacetSchema(schema_id=COVERAGE_SCHEMA_ID, schema_version=COVERAGE_SCHEMA_VERSION, facets=[
    _coverage_facet(10, "goal", "Goal and core value", "Problem, affected stakeholder, and core value."),
    _coverage_facet(20, "users", "Stakeholder context", "Primary and supporting stakeholders and operating context."),
    _coverage_facet(30, "flows", "Operational scenarios", "Trigger-to-outcome scenarios, ordered actions, and exceptions."),
    _coverage_facet(40, "data", "Data model and sources", "Data, location, and ownership."),
    _coverage_facet(50, "integrations", "Integrations", "Named systems and APIs."),
    _coverage_facet(60, "nfrs", "Quality needs", "Founder-visible quality impact and measurable targets."),
    _coverage_facet(70, "failures", "Failure modes", "Breakage, degradation, and forbidden outcomes."),
    _coverage_facet(80, "constraints", "Constraints", "Budget, schedule, team, and technology affinity."),
    _coverage_facet(90, "risks", "Risks", "Assumptions that threaten viability."),
    _coverage_facet(100, "done", "Done criteria", "Observable completion and success criteria."),
    _coverage_facet(110, "glossary", "Glossary", "Founder domain terms and meanings."),
])
