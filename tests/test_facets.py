from uuid import uuid4
import pytest
from pydantic import ValidationError
from vmodel_contracts.facets import (
    COVERAGE_SCHEMA, EXTERNAL_OPTION_ID, DeadLetterEntry, DeadLetterReason,
    FacetDefinition, FacetOption, PromotionReview, PromotionStatus,
)


def test_every_coverage_facet_has_external_lane_and_stable_ids():
    assert len(COVERAGE_SCHEMA.facets) == 11
    assert len({f.facet_id for f in COVERAGE_SCHEMA.facets}) == 11
    for facet in COVERAGE_SCHEMA.facets:
        assert any(o.option_id == EXTERNAL_OPTION_ID and o.key == 'external' for o in facet.options)


def test_facet_without_external_is_rejected():
    with pytest.raises(ValidationError):
        FacetDefinition(facet_id=1,key='goal',label='Goal',definition='Goal',options=[
            FacetOption(option_id=1,key='known',label='Known',definition='Known')])


def test_dlq_is_evidence_not_schema_mutation():
    entry=DeadLetterEntry(dlq_id=uuid4(),evidence_id=uuid4(),run_id='r',session_id='s',
        schema_id='interview.coverage',schema_version='1.0.0',reason=DeadLetterReason.UNSOLICITED_FACET,
        raw_text='Our SLA must be 99.95%.',proposed_facet_key='service_level',created_at='2026-09-22T08:00:00Z')
    assert entry.reason is DeadLetterReason.UNSOLICITED_FACET
    assert 'facets' not in entry.model_dump()


def test_promotion_cannot_be_accepted_without_human_review_evidence():
    with pytest.raises(ValidationError):
        PromotionReview(proposal_id=uuid4(),source_dlq_ids=[uuid4()],status=PromotionStatus.ACCEPTED,
            target_schema_id='interview.coverage',target_schema_version='1.1.0')
