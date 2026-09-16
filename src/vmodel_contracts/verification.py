"""Verification loop contracts: the right arm of the V.

Design line (hybrid B+C): everything checkable deterministically is checked
deterministically (test execution in the founder's own environment, AST /
static analysis, embeddings-based traceability, schema validation). The LLM
judges only the semantic residue: things that are genuinely a matter of
meaning.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import Field, model_validator

from .base import ContractModel


class VModelLevel(str, Enum):
    """The V's test hierarchy, mirroring the spec hierarchy."""

    UNIT = "unit"
    MODULE = "module"
    SYSTEM = "system"
    ACCEPTANCE = "acceptance"   # against the original needs (AcceptanceCriterion)


class TestCase(ContractModel):
    """One row in a data-driven or scenario-matrix test."""

    name: str
    inputs: list[str]
    expected_outcomes: list[str]


class TestExecution(ContractModel):
    """Known machine-readable runner inputs.

    Fields are optional because they apply to different runners, but unknown
    ad-hoc keys are forbidden by ContractModel. Human-readable procedure text
    stays separate, so adding automation detail cannot crowd it out.
    """

    url: str | None = None
    method: str | None = None
    body_json: str | None = None
    expected_status: int | None = None
    command: str | None = None
    expected_exit: int | None = None
    expected_stdout_contains: str | None = None
    selector: str | None = None


class TestDefinition(ContractModel):
    """Canonical procedure for every generated test.

    All fields are always present (empty lists are honest when a phase does
    not apply). `cases` preserves useful matrices without allowing their keys
    to replace the procedure contract. `execution` preserves the small
    machine-readable subset used by deterministic runners. The LLM owns the
    technical content; code owns only its stable container.
    """

    @model_validator(mode="before")
    @classmethod
    def supply_empty_execution_container(cls, data):
        """Keep the code-owned execution container stable when no metadata exists.

        Forced function calls strongly constrain DeepSeek's shape but do not
        guarantee every required nested argument. Missing ``execution`` carries
        no model-authored substance: its canonical honest value is an empty
        TestExecution, unlike missing procedure steps or outcomes.
        """
        if isinstance(data, dict) and "execution" not in data:
            data = {**data, "execution": {}}
        return data

    preconditions: list[str]
    steps: list[str]
    expected_outcomes: list[str]
    cleanup: list[str]
    cases: list[TestCase]
    execution: TestExecution


class AcceptanceTest(ContractModel):
    """A runnable check. `runner` tells the founder-side agent how to execute
    it IN THE FOUNDER'S OWN ENVIRONMENT - we never run their code on our infra."""

    test_id: str = Field(pattern=r"^T-\d+$")
    level: VModelLevel
    criterion_id: str | None = Field(default=None, description="AC-id this test realizes (acceptance level).")
    spec_id: str | None = Field(default=None, description="SPEC-id this test targets (lower levels).")
    description: str
    runner: str = Field(description="'http' | 'dom' | 'cli' | 'static' | 'semantic'")
    definition: TestDefinition


class TestResult(ContractModel):
    test_id: str
    passed: bool
    evidence: str = Field(description="What the runner observed: status code, diff excerpt, static-analysis finding.")
    ran_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DivergenceKind(str, Enum):
    MISSING_CAPABILITY = "missing_capability"       # spec says it, product doesn't have it
    CONTRADICTS_SPEC = "contradicts_spec"           # product does the opposite of the spec
    UNVERIFIABLE = "unverifiable"                   # cannot be checked deterministically, LLM unsure
    SPEC_GAP = "spec_gap"                           # product behavior nobody specified


class Divergence(ContractModel):
    """One finding the founder should care about. The demo's success criterion
    is finding at least one of these in a real run."""

    kind: DivergenceKind
    summary: str
    detail: str
    requirement_id: str | None = None
    test_id: str | None = None
    severity: str = Field(description="'blocking' | 'important' | 'nice-to-have'")
    detection: str = Field(description="'deterministic' | 'llm_judged' - provenance of every finding.")


class VerificationVerdict(str, Enum):
    CONFORMS = "conforms"
    DIVERGES = "diverges"
    INCOMPLETE = "incomplete"   # verification itself could not finish


class VerificationReport(ContractModel):
    session_id: str
    target_ref: str = Field(description="What was verified: deployed URL, repo ref, or founder-env session id.")
    results: list[TestResult]
    divergences: list[Divergence]
    verdict: VerificationVerdict
    semantic_residue_notes: list[str] = Field(
        default_factory=list,
        description="Things only an LLM/human can judge (tone, flow coherence), with the LLM's reading.",
    )

