"""Code-owned source evidence. Integrity is not authorship or semantic support."""
from typing import Any
from pydantic import Field, model_validator
from .semantic_review import ReviewModel, digest


class FounderDecisionCitation(ReviewModel):
    """Exact recorded item at selection time, including its resolution history.

    source_revision hashes the whole snapshot, not the ADR or its rationale.
    A matching hash proves neither that an ADR follows the source nor that the
    founder chose the architecture. Those are separate review questions.
    """
    source_ref: str = Field(min_length=1, max_length=200)
    source_revision: str = Field(pattern=r'^[a-f0-9]{64}$')
    source: dict[str, Any]

    @model_validator(mode='after')
    def bound_source(self):
        if self.source.get('item_id') != self.source_ref:
            raise ValueError('citation ref does not match the recorded source')
        if self.source.get('status') != 'decided' or any(
            not isinstance(self.source.get(key), str) or not self.source[key].strip()
            for key in ('decision', 'reason')
        ):
            raise ValueError('citation requires a decided source with decision and reason')
        if digest(self.source) != self.source_revision:
            raise ValueError('citation revision does not match the exact source snapshot')
        return self
