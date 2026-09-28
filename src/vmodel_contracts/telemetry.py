"""Per-stage token/cost logging. A LAUNCH REQUIREMENT, not later telemetry:
the business case ($5 per full run) is an arithmetic estimate until these
records exist for real runs.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from pydantic import Field

from .base import ContractModel

# Versioned price table (USD per MTok). THE one table for every repo (shared-
# module doctrine: it lived in interview-engine AND spec-generator with
# divergent failure behavior - a missing price crashed one pipeline and was
# silently zeroed in the other). Update here AND bump PRICE_TABLE_VERSION -
# price drift is real and silent drift makes cost reports lie retroactively.
PRICE_TABLE_VERSION = "2026-09-12"
PRICES_USD_PER_MTOK: dict[str, tuple[float, float]] = {
    # model: (input, output)
    "deepseek-flash": (0.30, 1.20),       # V4.1 Flash peak; off-peak $0.15/$0.60
    "deepseek-v4-pro": (1.32, 3.96),      # peak; off-peak $0.66/$1.98; retires to Flash 2026-09-14
    "claude-sonnet-5": (2.00, 10.00),     # platform.claude.com, 2026-09-08
    "claude-haiku-4.5": (1.00, 5.00),     # platform.claude.com, 2026-09-08
    "gpt-5": (1.25, 10.00),               # OpenAI model page, 2026-09-08
    "gpt-5-mini": (0.25, 2.00),
    "gpt-5-nano": (0.05, 0.40),
}


def load_price_table() -> dict[str, tuple[float, float]]:
    """Built-in defaults, overridable without a code change: point
    VMODEL_PRICE_TABLE at a JSON file {"model": [input_per_mtok, output_per_mtok], ...}.
    The operator's file WINS on conflict, so correcting a price is a config
    edit, not a release."""
    table = dict(PRICES_USD_PER_MTOK)
    path = os.environ.get("VMODEL_PRICE_TABLE")
    if path:
        with open(Path(path)) as f:
            override = json.load(f)
        for model, pair in override.items():
            if not (isinstance(pair, list) and len(pair) == 2):
                raise ValueError(f"VMODEL_PRICE_TABLE entry {model!r} must be [input, output] per MTok")
            table[model] = (float(pair[0]), float(pair[1]))
    return table


def price_for(model: str, provider: str = "") -> tuple[float, float]:
    """(input, output) USD per MTok for one call. Local by construction, not
    by table lookup: any ollama-routed call is $0 however the provider string
    is spelled ('ollama', langchain's 'chatollama', a bare local model name
    routed through the ollama config). The hard-fail is reserved for UNPRICED
    REMOTE calls - a missing price for a paid model means an unbudgeted call,
    and that must crash loudly, never log a silent $0."""
    p = (provider or "").lower()
    if "ollama" in p or model.startswith(("ollama:", "ollama/")):
        return (0.0, 0.0)
    table = load_price_table()
    if model not in table:
        raise KeyError(
            f"no price for {model!r} in table v{PRICE_TABLE_VERSION} - add it via "
            "VMODEL_PRICE_TABLE; unpriced calls are unbudgeted calls")
    return table[model]


class StageTokenUsage(ContractModel):
    """One LLM call stage's measured usage. Deterministic stages log nothing
    here - their cost is compute, tracked separately."""

    session_id: str
    route_version: int | None = Field(default=None, ge=0, description="Interview route segment; null for historical or unassigned calls")
    stage: str = Field(description="'interview' | 'intent_distillation' | 'requirements' | 'spec_authoring' | 'semantic_residue' | ...")
    provider: str = Field(description="'deepseek' | 'openai' | 'anthropic' | ...")
    model: str
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    cached_tokens: int = Field(default=0, ge=0)
    price_per_mtok_prompt_usd: float | None = Field(description="Price at call time; null when the provider has not published an authoritative price.")
    price_per_mtok_completion_usd: float | None
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def cost_usd(self) -> float | None:
        if self.price_per_mtok_prompt_usd is None or self.price_per_mtok_completion_usd is None:
            return None
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
