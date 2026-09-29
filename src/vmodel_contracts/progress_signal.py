"""Versioned, append-only observations. These never authorize a control action."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProgressSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1] = 1
    event_id: str = Field(min_length=1)
    cursor: int = Field(ge=1)
    task_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    phase_key: str = Field(min_length=1)
    stage: str = Field(min_length=1)
    label: str = Field(min_length=1, max_length=240)
    status: Literal["started", "completed", "failed", "heartbeat", "item_started", "item_completed"]
    detail: str | None = Field(default=None, max_length=800)
    completed: int | None = Field(default=None, ge=0)
    total: int | None = Field(default=None, ge=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def check_counts(self):
        if self.completed is not None and self.total is not None and self.completed > self.total:
            raise ValueError("completed exceeds total")
        return self


class ProgressPage(BaseModel):
    events: list[ProgressSignal]
    next_cursor: int = Field(ge=0)
