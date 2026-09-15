"""Canonical artifact lifecycle vocabulary and guarded transitions.

This is deliberately not a workflow engine. It defines the states, legal arcs,
guards, audit record, and diagrams shared by every V-model module. Storage and
orchestration remain consumer concerns in phase 1.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import Field, model_validator

from .base import ContractModel


class ArtifactState(str, Enum):
    MISSING = "missing"
    PARTIAL = "partial"
    COMPLETE = "complete"
    STALE = "stale"
    INVALIDATED = "invalidated"
    MIGRATED = "migrated"


class LifecycleTransition(str, Enum):
    BEGIN = "begin"
    CHECKPOINT = "checkpoint"
    FINALIZE = "finalize"
    DEPENDENCY_CHANGED = "dependency_changed"
    INVALIDATE = "invalidate"
    RESTART = "restart"
    MIGRATE = "migrate"
    ADOPT_MIGRATION = "adopt_migration"
    RESUME = "resume"
    DELETE = "delete"


TRANSITION_TABLE: dict[LifecycleTransition, tuple[frozenset[ArtifactState], ArtifactState]] = {
    LifecycleTransition.BEGIN: (frozenset({ArtifactState.MISSING}), ArtifactState.PARTIAL),
    LifecycleTransition.CHECKPOINT: (frozenset({ArtifactState.PARTIAL}), ArtifactState.PARTIAL),
    LifecycleTransition.FINALIZE: (frozenset({ArtifactState.PARTIAL}), ArtifactState.COMPLETE),
    LifecycleTransition.DEPENDENCY_CHANGED: (frozenset({ArtifactState.COMPLETE}), ArtifactState.STALE),
    LifecycleTransition.INVALIDATE: (frozenset({ArtifactState.PARTIAL, ArtifactState.COMPLETE, ArtifactState.STALE}), ArtifactState.INVALIDATED),
    LifecycleTransition.RESTART: (frozenset({ArtifactState.INVALIDATED}), ArtifactState.PARTIAL),
    LifecycleTransition.MIGRATE: (frozenset({ArtifactState.COMPLETE, ArtifactState.STALE}), ArtifactState.MIGRATED),
    LifecycleTransition.ADOPT_MIGRATION: (frozenset({ArtifactState.MIGRATED}), ArtifactState.COMPLETE),
    LifecycleTransition.RESUME: (frozenset({ArtifactState.COMPLETE}), ArtifactState.PARTIAL),
    LifecycleTransition.DELETE: (frozenset(ArtifactState), ArtifactState.MISSING),
}


class LifecycleEvent(ContractModel):
    artifact_id: str = Field(min_length=1)
    artifact_kind: str = Field(min_length=1)
    transition: LifecycleTransition
    from_state: ArtifactState
    to_state: ArtifactState
    actor: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content_hash: str | None = None
    dependency_hashes: dict[str, str] = Field(default_factory=dict)
    anchor_hash: str | None = None
    producer_stage: str | None = None
    invalidates: list[str] = Field(default_factory=list)
    guard_evidence: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def legal_and_guarded(self):
        validate_transition(self)
        return self


def _require(event: LifecycleEvent, *keys: str) -> None:
    missing = [key for key in keys if event.guard_evidence.get(key) in (None, "", [], {}, False)]
    if missing:
        raise ValueError(f"{event.transition.value} guard missing evidence: {', '.join(missing)}")


def validate_transition(event: LifecycleEvent | dict) -> LifecycleEvent:
    """Validate one arc and its guard evidence; returns the typed event."""
    if not isinstance(event, LifecycleEvent):
        # Avoid recursive model validation: construct only after validating the
        # enum-bearing shell through normal initialization.
        return LifecycleEvent.model_validate(event)
    sources, destination = TRANSITION_TABLE[event.transition]
    if event.from_state not in sources or event.to_state != destination:
        allowed = ", ".join(sorted(s.value for s in sources))
        raise ValueError(
            f"illegal {event.transition.value} transition: {event.from_state.value} -> {event.to_state.value}; "
            f"expected [{allowed}] -> {destination.value}"
        )
    t = event.transition
    if t == LifecycleTransition.BEGIN:
        _require(event, "producer_owns_artifact", "inputs_recorded", "anchor_recorded")
    elif t == LifecycleTransition.CHECKPOINT:
        _require(event, "monotonic_progress", "same_inputs", "same_anchor")
    elif t == LifecycleTransition.FINALIZE:
        _require(event, "schema_valid", "complete", "hashes_sealed")
        if not event.content_hash:
            raise ValueError("finalize guard requires content_hash")
    elif t == LifecycleTransition.DEPENDENCY_CHANGED:
        _require(event, "changed_dependency")
    elif t == LifecycleTransition.INVALIDATE:
        _require(event, "named_boundary", "downstream_closure_computed")
    elif t == LifecycleTransition.RESTART:
        _require(event, "producer_rerun_started", "current_inputs")
    elif t == LifecycleTransition.MIGRATE:
        _require(event, "approved_migrator", "source_hash", "source_version", "target_schema_valid")
    elif t == LifecycleTransition.ADOPT_MIGRATION:
        _require(event, "canonical_storage_updated", "checkpoint_updated", "atomic", "hashes_agree")
    elif t == LifecycleTransition.RESUME:
        _require(event, "named_next_artifact", "legal_outgoing_arc")
    elif t == LifecycleTransition.DELETE:
        _require(event, "explicit_destructive_operation")
    return event


def append_lifecycle_event(path: str | Path, event: LifecycleEvent | dict) -> LifecycleEvent:
    """Validate and append one JSON line. Existing bytes are never rewritten."""
    typed = validate_transition(event)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as stream:
        stream.write(typed.model_dump_json() + "\n")
        stream.flush()
    return typed


def mermaid_diagram() -> str:
    lines = ["stateDiagram-v2", "    [*] --> missing"]
    for transition, (sources, destination) in TRANSITION_TABLE.items():
        for source in sorted(sources, key=lambda x: x.value):
            lines.append(f"    {source.value} --> {destination.value}: {transition.value}")
    return "\n".join(lines) + "\n"


def dot_diagram() -> str:
    lines = ["digraph artifact_lifecycle {", "  rankdir=LR;"]
    for transition, (sources, destination) in TRANSITION_TABLE.items():
        for source in sorted(sources, key=lambda x: x.value):
            lines.append(f'  "{source.value}" -> "{destination.value}" [label="{transition.value}"];')
    lines.append("}")
    return "\n".join(lines) + "\n"
