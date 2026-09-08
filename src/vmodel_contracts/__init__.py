"""vmodel-contracts: the only artifact allowed to cross module boundaries.

Modules (interview-engine, spec-generator, verification-loop, delivery-api)
never import each other. They exchange these models, pinned to an exact
release of this package.
"""
from .version import CONTRACT_VERSION
from .intake import AppArchetype, IntakeSubmission, ScopeVerdict
from .compat import ContractVersionMismatch, check_compatible
from .interview import Assumption, IntentNeed, InterviewTurn, InterviewTranscript, IntentModel, ScopeExclusion
from .needs import StakeholderNeed, StakeholderNeedsSet
from .requirements import AcceptanceCriterion, Priority, Requirement, RequirementKind, RequirementSet
from .architecture import ArchitectureDecision, ArchitectureOverview, ComponentSpec
from .spec import (
    BuildMilestone,
    ItemSpec,
    SpecItemKind,
    PunchListItem,
    SpecBundle,
    SpecManifest,
    TraceabilityEntry,
)
from .verification import (
    AcceptanceTest,
    Divergence,
    DivergenceKind,
    TestResult,
    VerificationReport,
    VerificationVerdict,
    VModelLevel,
)
from .delivery import DeliveryBundle, HandoffFormat, RunLink, RunState, RunStatus
from .telemetry import RunCostReport, StageTokenUsage

__all__ = [
    "CONTRACT_VERSION", "check_compatible", "ContractVersionMismatch",
    "AppArchetype",
    "IntakeSubmission",
    "ScopeVerdict",
    "InterviewTurn",
    "InterviewTranscript",
    "IntentModel",
    "Assumption",
    "ScopeExclusion", "IntentNeed",
    "StakeholderNeed",
    "StakeholderNeedsSet",
    "AcceptanceCriterion",
    "Priority",
    "Requirement", "RequirementKind",
    "RequirementSet",
    "ArchitectureDecision",
    "ArchitectureOverview",
    "ComponentSpec",
    "BuildMilestone",
    "ItemSpec",
    "SpecItemKind",
    "PunchListItem",
    "SpecBundle",
    "SpecManifest",
    "TraceabilityEntry",
    "AcceptanceTest",
    "Divergence",
    "DivergenceKind",
    "TestResult",
    "VerificationReport",
    "VerificationVerdict",
    "VModelLevel",
    "DeliveryBundle",
    "HandoffFormat",
    "RunLink",
    "RunState",
    "RunStatus",
    "RunCostReport",
    "StageTokenUsage",
]
