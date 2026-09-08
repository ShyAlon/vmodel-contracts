"""Per-stage token/cost logging. A LAUNCH REQUIREMENT, not later telemetry:
the business case ($5 per full run) is an arithmetic estimate until these
records exist for real runs.
"""
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import Field

from .base import ContractModel


class StageTokenUsage(ContractModel):
    """One LLM call stage's measured usage. Deterministic stages log nothing
    here - their cost is compute, tracked separately."""

    session_id: str
    stage: str = Field(description="'interview' | 'intent_distillation' | 'requirements' | 'spec_authoring' | 'semantic_residue' | ...")
    provider: str = Field(description="'deepseek' | 'openai' | 'anthropic' | ...")
    model: str
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    cached_tokens: int = Field(default=0, ge=0)
    price_per_mtok_prompt_usd: float = Field(description="Price at call time, from the versioned price table.")
    price_per_mtok_completion_usd: float
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def cost_usd(self) -> float:
        return (
            self.prompt_tokens * self.price_per_mtok_prompt_usd
            + self.completion_tokens * self.price_per_mtok_completion_usd
        ) / 1_000_000


class RunCostReport(ContractModel):
    """One full run's measured cost. This is what turns '$5 per spec' from a
    belief into a number."""

    session_id: str
    stages: list[StageTokenUsage]
    total_cost_usd: float
    deterministic_compute_seconds: float = Field(
        default=0.0, description="Wall time spent in deterministic stages (test execution, AST, embeddings)."
    )
    llm_call_count: int
