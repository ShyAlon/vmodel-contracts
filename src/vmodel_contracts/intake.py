"""Intake + scope gate.

The system builds specs for interactive applications - including games -
delivered on web or mobile platforms. Intake classifies; non-software ideas
and unsupported delivery forms get a polite decline. The
gate is hybrid by design: deterministic signals first, LLM only as tiebreaker.
"""
from __future__ import annotations

from enum import Enum

from pydantic import Field

from .base import ContractModel


class AppArchetype(str, Enum):
    """Legacy-named application archetypes the product knows how to spec.

    OTHER_WEB and NOT_WEB_APP are retained machine values for payload
    compatibility. Renaming them requires a contract migration; they now mean
    other supported interactive application and out-of-scope respectively.
    """

    SAAS_CRUD = "saas_crud"            # classic multi-tenant CRUD SaaS
    MARKETPLACE = "marketplace"        # two-sided listings + transactions
    CONTENT_SITE = "content_site"      # CMS-driven publishing
    DASHBOARD = "dashboard"            # analytics over external APIs
    ECOMMERCE = "ecommerce"            # catalog + cart + payment
    OTHER_WEB = "other_web"            # legacy value: supported interactive app, no narrower archetype
    NOT_WEB_APP = "not_web_app"        # legacy value: out of product scope -> decline


class IntakeSubmission(ContractModel):
    """What the founder hands us before the interview starts."""

    free_text: str = Field(description="Founder's own description of the product, unedited.")
    known_answers: dict[str, str] = Field(
        default_factory=dict,
        description="Any structured answers already collected (target users, platforms, integrations).",
    )
    founder_id: str = Field(description="Opaque founder identifier from delivery-api.")
    submission_id: str


class ScopeVerdict(ContractModel):
    """The gate's decision. `accepted=False` ends the run politely."""

    submission_id: str
    accepted: bool
    archetype: AppArchetype
    confidence: float = Field(ge=0.0, le=1.0)
    deterministic_signals: list[str] = Field(
        description="Auditable signals the deterministic classifier fired on (e.g. 'mentions mobile app store')."
    )
    llm_tiebreak_used: bool = Field(
        description="True only when deterministic classification was inconclusive and the LLM tiebreaker ran."
    )
    decline_message: str | None = Field(
        default=None,
        description="Polite, specific explanation shown to the founder when accepted=False.",
    )
