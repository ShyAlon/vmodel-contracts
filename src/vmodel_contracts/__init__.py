"""vmodel-contracts: the only artifact allowed to cross module boundaries.

Modules (interview-engine, spec-generator, verification-loop, delivery-api)
never import each other. They exchange these models, pinned to an exact
release of this package.
"""
from .version import CONTRACT_VERSION
from .runtime import keep_awake_command, run_with_system_awake, system_awake
from .intake import AppArchetype, IntakeSubmission, ScopeVerdict
from .compat import ContractVersionMismatch, check_compatible
from .interview import (
    Assumption, IntentNeed, InterviewTurn, InterviewTranscript, IntentModel, ScopeExclusion,
    TechArea, TechPreference, TechStrength,
)
from .conops import (ConceptDecision, ConceptOption, ConOpsDocument, OperationalScenario, StakeholderContext)
from .needs import StakeholderNeed, StakeholderNeedsSet
from .requirements import AcceptanceCriterion, Priority, Requirement, RequirementKind, RequirementSet
from .architecture import ArchitectureDecision, ArchitectureOverview, ComponentSpec, StackEntry
from .baseline import BaselineMode, RepositoryManifest, SystemBaseline
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
    TestCase,
    TestDefinition,
    TestExecution,
    Divergence,
    DivergenceKind,
    TestResult,
    VerificationReport,
    VerificationVerdict,
    VModelLevel,
)
from .delivery import DeliveryBundle, HandoffFormat, RunLink, RunState, RunStatus
from .srs import SRSDocument
from .telemetry import (PRICE_TABLE_VERSION, PRICES_USD_PER_MTOK, RunCostReport,
                        StageTokenUsage, load_price_table, price_for)
from . import text_qa

__all__ = [
    "CONTRACT_VERSION", "check_compatible", "ContractVersionMismatch",
    "keep_awake_command", "run_with_system_awake", "system_awake",
    "AppArchetype",
    "IntakeSubmission",
    "ScopeVerdict",
    "InterviewTurn",
    "InterviewTranscript",
    "IntentModel",
    "Assumption",
    "ScopeExclusion", "TechArea", "TechPreference", "TechStrength", "IntentNeed",
    "ConOpsDocument", "StakeholderContext", "OperationalScenario",
    "ConceptOption", "ConceptDecision",
    "StakeholderNeed",
    "StakeholderNeedsSet",
    "AcceptanceCriterion",
    "Priority",
    "Requirement", "RequirementKind",
    "RequirementSet",
    "ArchitectureDecision",
    "ArchitectureOverview",
    "ComponentSpec",
    "StackEntry",
    "BaselineMode", "RepositoryManifest", "SystemBaseline",
    "BuildMilestone",
    "ItemSpec",
    "SpecItemKind",
    "PunchListItem",
    "SpecBundle",
    "SpecManifest",
    "TraceabilityEntry",
    "AcceptanceTest",
    "TestCase",
    "TestDefinition",
    "TestExecution",
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
    "SRSDocument",
    "RunCostReport",
    "StageTokenUsage",
    "PRICE_TABLE_VERSION",
    "PRICES_USD_PER_MTOK",
    "load_price_table",
    "price_for",
    "text_qa",
]


