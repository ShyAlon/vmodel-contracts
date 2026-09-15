"""Canonical cross-module V-model vocabulary.

Machine values are stable identifiers. Labels and filenames are the only
human-facing spellings modules/scripts should use; consumers must not invent
aliases for these cross-boundary terms.
"""
from __future__ import annotations

from enum import Enum


class PipelineStage(str, Enum):
    INTAKE = "intake"
    INTERVIEW = "interview"
    INTENT = "intent"
    SCOPE_TIEBREAK = "scope_tiebreak"
    PROBING = "probing"
    DISTILLATION = "distillation"
    PHRASING = "phrasing"
    CONOPS = "conops"
    NEEDS = "needs"
    SRS = "srs"
    ARCHITECTURE = "architecture"
    ITEMS = "items"
    TESTS = "tests"
    REVIEW = "review"
    ASSEMBLE = "assemble"
    VERIFICATION = "verification"
    DELIVERY = "delivery"


STAGE_LABELS: dict[PipelineStage, str] = {
    PipelineStage.INTAKE: "Intake",
    PipelineStage.INTERVIEW: "Interview",
    PipelineStage.INTENT: "Intent Model",
    PipelineStage.SCOPE_TIEBREAK: "Scope Tiebreak",
    PipelineStage.PROBING: "Interview Probing",
    PipelineStage.DISTILLATION: "Intent Distillation",
    PipelineStage.PHRASING: "Question Phrasing",
    PipelineStage.CONOPS: "Concept of Operations",
    PipelineStage.NEEDS: "Stakeholder Needs",
    PipelineStage.SRS: "Software Requirements Specification",
    PipelineStage.ARCHITECTURE: "Architecture",
    PipelineStage.ITEMS: "Item Specifications",
    PipelineStage.TESTS: "Acceptance Tests",
    PipelineStage.REVIEW: "Review",
    PipelineStage.ASSEMBLE: "Assembly",
    PipelineStage.VERIFICATION: "Verification",
    PipelineStage.DELIVERY: "Delivery",
}


class ArtifactName(str, Enum):
    INTERVIEW_TRANSCRIPT = "interview_transcript.json"
    INTENT_MODEL = "intent_model.json"
    CONOPS = "conops.json"
    NEEDS = "needs.json"
    SRS = "srs.json"
    ARCHITECTURE = "architecture.json"
    ITEMS = "items.json"
    TESTS = "tests.json"
    MANIFEST = "manifest.json"
    TRACEABILITY = "traceability.json"


ARTIFACT_LABELS: dict[ArtifactName, str] = {
    ArtifactName.INTERVIEW_TRANSCRIPT: "Interview Transcript",
    ArtifactName.INTENT_MODEL: "Intent Model",
    ArtifactName.CONOPS: "Concept of Operations",
    ArtifactName.NEEDS: "Stakeholder Needs",
    ArtifactName.SRS: "Software Requirements Specification",
    ArtifactName.ARCHITECTURE: "Architecture",
    ArtifactName.ITEMS: "Item Specifications",
    ArtifactName.TESTS: "Acceptance Tests",
    ArtifactName.MANIFEST: "Manifest",
    ArtifactName.TRACEABILITY: "Traceability Matrix",
}

# Canonical terms. "CONOPS" is the stable stage id/acronym; human prose uses
# the expanded label "Concept of Operations" on first/reference use.
CONCEPT_OF_OPERATIONS = STAGE_LABELS[PipelineStage.CONOPS]
CONCEPT_OPTION = "concept option"
CONCEPT_DECISION = "concept decision"
OPERATIONAL_SCENARIO = "operational scenario"
STAKEHOLDER_CONTEXT = "stakeholder context"


CANONICAL_STAGE_IDS: frozenset[str] = frozenset(stage.value for stage in PipelineStage)
