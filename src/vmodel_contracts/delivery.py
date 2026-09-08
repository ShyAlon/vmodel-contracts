"""Delivery: what the founder walks away with."""
from __future__ import annotations

from enum import Enum

from pydantic import Field

from .base import ContractModel


class HandoffFormat(str, Enum):
    GIT_REPO = "git_repo"           # spec bundle as a repo the founder points their coding agent at
    ZIP_ARCHIVE = "zip_archive"
    MARKDOWN_PACK = "markdown_pack" # single downloadable pack


class DeliveryBundle(ContractModel):
    session_id: str
    spec_bundle_ref: str = Field(description="Storage reference to the SpecBundle payload.")
    verification_report_ref: str | None = Field(
        default=None, description="Present when the founder already ran verification against an implementation."
    )
    handoff_format: HandoffFormat
    artifact_url: str | None = Field(default=None, description="Where the founder retrieves the deliverable.")
    expires_at: str | None = None


class RunState(str, Enum):
    """The run state machine delivery-api owns. Background jobs, never
    request/response - Vercel's 300s function cap made that call."""

    CREATED = "created"
    IN_INTERVIEW = "in_interview"
    INTENT_REVIEW = "intent_review"       # founder review gate: cheapest place to catch a misunderstanding
    GENERATING = "generating"
    DELIVERED = "delivered"
    VERIFYING = "verifying"
    REPORTED = "reported"
    DECLINED_OUT_OF_SCOPE = "declined_out_of_scope"
    BUDGET_STOPPED = "budget_stopped"     # hard stop fired


class RunLink(ContractModel):
    """One personal link per tester. No accounts in the demo: the token gates
    the run, ties interview/spec/verification together, and rate-limits."""

    token: str = Field(description="Opaque, unguessable. The link IS the credential.")
    run_id: str
    founder_label: str = Field(description="Shy's label for the tester; no PII required.")
    active: bool = True


class RunStatus(ContractModel):
    run_id: str
    state: RunState
    cost_report_ref: str | None = None
    token_budget_usd: float = Field(description="Per-run hard cap; delivery-api enforces it per stage.")
