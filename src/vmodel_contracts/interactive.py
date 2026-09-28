"""Versioned HTTP contracts for engine orchestration.

Human text is payload, never control state. Consumers branch only on these
integer enums, protocol versions, identifiers, sequence numbers, and HTTP
status classes.
"""
from __future__ import annotations

from enum import IntEnum
from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

INTERACTIVE_PROTOCOL_VERSION = 1


class InteractiveModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class EventType(IntEnum):
    RUN_STARTED = 10
    PHASE_STARTED = 20
    PHASE_PROGRESS = 21
    PHASE_COMPLETED = 22
    INPUT_REQUESTED = 30
    INPUT_ACCEPTED = 31
    ARTIFACT_PRODUCED = 40
    USAGE_RECORDED = 50
    ROUTE_CHANGED = 51
    RUN_COMPLETED = 60
    RUN_FAILED = 61
    HEARTBEAT = 70


class InputKind(IntEnum):
    TEXT = 1
    CHOICE = 2
    APPROVAL = 3


class ProcessStatus(IntEnum):
    CREATED = 10
    RUNNING = 20
    WAITING_INPUT = 30
    COMPLETED = 40
    FAILED = 50
    INCOMPATIBLE = 60


class NextStep(IntEnum):
    NONE = 0
    RUN = 10
    WAIT_INPUT = 20
    ADVANCE_PHASE = 30
    COMPLETE = 40
    STOP = 50
    RESTART_REQUIRED = 60


class ProtocolErrorCode(IntEnum):
    UNSUPPORTED_VERSION = 100
    INVALID_SEQUENCE = 110
    UNKNOWN_INPUT = 120
    STALE_INPUT = 121
    DUPLICATE_RESPONSE = 122
    INVALID_RESPONSE = 130
    ROUTE_SWITCH_CONFLICT = 140
    INTERNAL_ERROR = 500


class InputOption(InteractiveModel):
    value: int | str
    label: str = Field(min_length=1)
    summary: str | None = None
    advantages: list[str] = Field(default_factory=list)
    disadvantages: list[str] = Field(default_factory=list)


class InputRequest(InteractiveModel):
    input_id: UUID
    kind: InputKind
    prompt: str = Field(min_length=1)
    options: list[InputOption] = Field(default_factory=list)
    rationale_required: bool = False
    context: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_options(self):
        if self.kind in (InputKind.CHOICE, InputKind.APPROVAL) and not self.options:
            raise ValueError("choice and approval inputs require options")
        if self.kind == InputKind.TEXT and self.options:
            raise ValueError("text inputs cannot declare options")
        return self


class InputResponse(InteractiveModel):
    protocol_version: Literal[INTERACTIVE_PROTOCOL_VERSION] = INTERACTIVE_PROTOCOL_VERSION
    input_id: UUID
    value: int | str | bool
    rationale: str | None = None
    actor_id: str = Field(min_length=1)


class ProgressPayload(InteractiveModel):
    completed: int = Field(ge=0)
    total: int | None = Field(default=None, ge=0)


class FailurePayload(InteractiveModel):
    code: ProtocolErrorCode
    detail: str
    retryable: bool = False


class ModelRouteSwitchRequest(InteractiveModel):
    model_route: Literal["ollama", "deepseek"]
    model: str = Field(min_length=1, max_length=160)
    expected_sequence: int = Field(ge=0)
    expected_input_id: UUID
    idempotency_key: UUID
    actor_id: str = Field(min_length=1)


class RouteChangePayload(InteractiveModel):
    actor_id: str
    from_route: str
    to_route: str
    from_model_map: dict[str, tuple[str, str]]
    to_model_map: dict[str, tuple[str, str]]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    route_version: int = Field(ge=1)
    session_sequence: int = Field(ge=1)
    idempotency_key: UUID


class InteractiveEvent(InteractiveModel):
    protocol_version: Literal[INTERACTIVE_PROTOCOL_VERSION] = INTERACTIVE_PROTOCOL_VERSION
    event_id: UUID
    session_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    phase_id: int = Field(ge=0)
    sequence: int = Field(ge=1)
    event_type: EventType
    process_status: ProcessStatus
    next_step: NextStep
    input_request: InputRequest | None = None
    progress: ProgressPayload | None = None
    failure: FailurePayload | None = None
    route_change: RouteChangePayload | None = None

    @model_validator(mode="after")
    def validate_event_payload(self):
        if (self.event_type == EventType.INPUT_REQUESTED) != (self.input_request is not None):
            raise ValueError("only input-requested events carry input_request")
        if self.process_status == ProcessStatus.WAITING_INPUT and self.next_step != NextStep.WAIT_INPUT:
            raise ValueError("waiting input requires WAIT_INPUT next step")
        if (self.event_type == EventType.ROUTE_CHANGED) != (self.route_change is not None):
            raise ValueError("route-change events require route_change payload")
        if self.event_type == EventType.RUN_FAILED and self.failure is None:
            raise ValueError("run-failed events require failure")
        return self


class EngineSnapshot(InteractiveModel):
    protocol_version: Literal[INTERACTIVE_PROTOCOL_VERSION] = INTERACTIVE_PROTOCOL_VERSION
    session_id: str
    task_id: str
    sequence: int = Field(ge=0)
    process_status: ProcessStatus
    next_step: NextStep
    open_input: InputRequest | None = None
    model_route: str | None = None
    model_map: dict[str, tuple[str, str]] | None = None
    route_version: int = 0
    route_history: list[RouteChangePayload] = Field(default_factory=list)


class StartSessionRequest(InteractiveModel):
    protocol_version: Literal[INTERACTIVE_PROTOCOL_VERSION] = INTERACTIVE_PROTOCOL_VERSION
    task_id: str = Field(min_length=1)
    idea: str = Field(min_length=1)
    model_route: str
    initial_model: str | None = None


class StartSessionResponse(InteractiveModel):
    snapshot: EngineSnapshot
    accepted_event: InteractiveEvent


class SubmitInputResponse(InteractiveModel):
    accepted_event: InteractiveEvent
    snapshot: EngineSnapshot


class ModelRouteSwitchResponse(InteractiveModel):
    accepted_event: InteractiveEvent
    snapshot: EngineSnapshot


class ProtocolError(InteractiveModel):
    protocol_version: Literal[INTERACTIVE_PROTOCOL_VERSION] = INTERACTIVE_PROTOCOL_VERSION
    code: ProtocolErrorCode
    detail: str
    retryable: bool = False
