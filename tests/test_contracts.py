"""Smoke tests: round-trip every model, verify version stamping, schema export."""
import json

from vmodel_contracts import (
    CONTRACT_VERSION,
    IntakeSubmission,
    IntentModel,
    Requirement,
    RequirementSet,
    AcceptanceCriterion,
    Priority,
    ScopeVerdict,
    AppArchetype,
    StageTokenUsage,
)
from vmodel_contracts.export_schema import all_models


def test_version_stamped_on_every_payload():
    sub = IntakeSubmission(free_text="A marketplace for surf lessons", founder_id="f1", submission_id="s1")
    assert sub.contract_version == CONTRACT_VERSION


def test_scope_verdict_decline_carries_message():
    v = ScopeVerdict(
        submission_id="s1",
        accepted=False,
        archetype=AppArchetype.NOT_WEB_APP,
        confidence=0.93,
        deterministic_signals=["mentions native iOS", "no web surface"],
        llm_tiebreak_used=False,
        decline_message="This builds specs for web applications only.",
    )
    assert not v.accepted and v.decline_message


def test_requirement_round_trip():
    r = Requirement(
        requirement_id="R-1",
        title="Users can book a lesson",
        statement="An end user books a surf lesson slot.",
        priority=Priority.MUST,
        acceptance=[AcceptanceCriterion(criterion_id="AC-1", statement="Booking returns a confirmation id")],
        need_ids=["N-1"],
        intent_fields=["in_scope"],
    )
    rs = RequirementSet(session_id="x", requirements=[r])
    assert rs.requirement_ids() == {"R-1"}
    assert RequirementSet.model_validate(rs.model_dump()).requirements[0].requirement_id == "R-1"


def test_cost_math():
    u = StageTokenUsage(
        session_id="x", stage="interview", provider="deepseek", model="deepseek-chat",
        prompt_tokens=100_000, completion_tokens=20_000,
        price_per_mtok_prompt_usd=2.0, price_per_mtok_completion_usd=10.0,
    )
    assert abs(u.cost_usd - 0.4) < 1e-9


def test_every_model_exports_schema():
    models = all_models()
    assert len(models) >= 20
    for name, m in models.items():
        schema = m.model_json_schema()
        assert "contract_version" in json.dumps(schema) or name == "ContractModel"
