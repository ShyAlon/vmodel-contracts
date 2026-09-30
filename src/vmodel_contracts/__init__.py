"""vmodel-contracts: the only artifact allowed to cross module boundaries.

Modules (interview-engine, spec-generator, verification-loop, delivery-api)
never import each other. They exchange these models, pinned to an exact
release of this package.
"""
from .version import CONTRACT_VERSION
from .facets import (
    EXTERNAL_OPTION_ID, COVERAGE_SCHEMA_ID, COVERAGE_SCHEMA_VERSION, COVERAGE_SCHEMA,
    FacetValueKind, EvidenceDisposition, DeadLetterReason, PromotionStatus, FacetOption,
    FacetDefinition, FacetSchema, SessionSchemaBinding, EvidenceRecord, DeadLetterEntry, PromotionReview,
)
from .vocabulary import (ARTIFACT_LABELS, CONCEPT_DECISION, CONCEPT_OF_OPERATIONS,
                         CONCEPT_OPTION, OPERATIONAL_SCENARIO, STAGE_LABELS, CANONICAL_STAGE_IDS,
                         STAKEHOLDER_CONTEXT, ArtifactName, PipelineStage)
from .product_scope import (PRODUCT_SCOPE_DEFINITION, SCOPE_DECLINE_PREFIX,
                            SCOPE_IN_SIGNALS, SCOPE_OUT_SIGNALS)
from .identity import CONCEPT_ALIASES, canonical_concept_id, canonical_technology_id, normalize_identity
from .runtime import keep_awake_command, run_with_system_awake, system_awake
from .intake import AppArchetype, IntakeSubmission, ScopeVerdict
from .intent_rubric import DELEGATION_DOCTRINE, INTENT_GATE_RUBRIC, intent_gate_instructions
from .artifact_lifecycle import (ArtifactState, LifecycleTransition, LifecycleEvent, TRANSITION_TABLE,
                                 validate_transition, append_lifecycle_event, mermaid_diagram, dot_diagram)
from .compat import ContractVersionMismatch, check_compatible
from .interview import (
    Assumption, IntentNeed, ResearchBrief, InterviewTurn, InterviewTranscript, IntentModel, ScopeExclusion,
    TechArea, TechPreference, TechStrength,
)
from .conops import (ConceptDecision, ConceptOption, ConOpsDocument, OperationalScenario, StakeholderContext)
from .needs import StakeholderNeed, StakeholderNeedsSet
from .requirements import AcceptanceCriterion, Priority, Requirement, RequirementKind, RequirementSet
from .architecture import ArchitectureDecision, ArchitectureOverview, TechnologySelection, ComponentSpec, StackEntry, StackEntryDisposition, StackEntryStatus
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
from .srs import SRSDocument, DesignConstraint
from .telemetry import (PRICE_TABLE_VERSION, PRICES_USD_PER_MTOK, RunCostReport,
                        StageTokenUsage, load_price_table, price_for)
from .runtime import AdaptiveCallWatchdog, AdaptiveWatchdogTimeout, parse_expert_verdict, format_expert_review_rounds, validate_expert_objections, classify_expert_objections
from . import text_qa

__all__ = [
    "CONTRACT_VERSION", "check_compatible", "ContractVersionMismatch",
    "PipelineStage", "STAGE_LABELS", "CANONICAL_STAGE_IDS", "ArtifactName", "ARTIFACT_LABELS",
    "CONCEPT_OF_OPERATIONS", "CONCEPT_OPTION", "CONCEPT_DECISION",
    "OPERATIONAL_SCENARIO", "STAKEHOLDER_CONTEXT",
    "PRODUCT_SCOPE_DEFINITION", "SCOPE_DECLINE_PREFIX", "SCOPE_IN_SIGNALS", "SCOPE_OUT_SIGNALS",
    "CONCEPT_ALIASES", "canonical_concept_id", "canonical_technology_id", "normalize_identity",
    "keep_awake_command", "run_with_system_awake", "system_awake",
    "ArtifactState", "LifecycleTransition", "LifecycleEvent", "TRANSITION_TABLE",
    "validate_transition", "append_lifecycle_event", "mermaid_diagram", "dot_diagram",
    "DELEGATION_DOCTRINE", "INTENT_GATE_RUBRIC", "intent_gate_instructions",
    "AppArchetype",
    "IntakeSubmission",
    "ScopeVerdict",
    "InterviewTurn",
    "InterviewTranscript",
    "IntentModel",
    "Assumption", "ResearchBrief",
    "ScopeExclusion", "TechArea", "TechPreference", "TechStrength", "IntentNeed",
    "ConOpsDocument", "StakeholderContext", "OperationalScenario",
    "ConceptOption", "ConceptDecision",
    "StakeholderNeed",
    "StakeholderNeedsSet",
    "AcceptanceCriterion",
    "Priority",
    "Requirement", "RequirementKind",
    "RequirementSet",
    "ArchitectureDecision", "TechnologySelection",
    "ArchitectureOverview",
    "ComponentSpec",
    "StackEntry", "StackEntryDisposition", "StackEntryStatus",
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
    "SRSDocument", "DesignConstraint",
    "RunCostReport",
    "StageTokenUsage",
    "PRICE_TABLE_VERSION",
    "PRICES_USD_PER_MTOK",
    "load_price_table",
    "price_for",
    "AdaptiveCallWatchdog", "AdaptiveWatchdogTimeout", "parse_expert_verdict", "format_expert_review_rounds", "validate_expert_objections", "classify_expert_objections",
    "text_qa",
    "IntegrityDiagnostic", "validate_traceability_graph",
]



from .bundle_integrity import IntegrityDiagnostic, validate_traceability_graph

from .decisions import founder_decision, binary_decision, emit_decision

from .interactive import (INTERACTIVE_PROTOCOL_VERSION, EngineSnapshot, EventType, FailurePayload,
    InputKind, InputOption, InputRequest, InputResponse, InteractiveEvent, NextStep, ProcessStatus,
    ProgressPayload, ProtocolError, ProtocolErrorCode, StartSessionRequest, StartSessionResponse,
    SubmitInputResponse)

from .semantic_review import SemanticFinding,ItemReviewDecision,SemanticReview,make_review
from .founder_register import FounderDecision,FounderRegister,FounderInputResolution,ConstraintAdvisory,apply_resolutions
from .handoff import CodingHandoff
__all__ += ["SemanticFinding","ItemReviewDecision","SemanticReview","make_review","FounderDecision","FounderRegister","FounderInputResolution","ConstraintAdvisory","apply_resolutions","CodingHandoff"]
