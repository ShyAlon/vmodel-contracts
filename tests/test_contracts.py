"""Smoke tests: round-trip every model, verify version stamping, schema export."""
import json

from vmodel_contracts import (
    CONTRACT_VERSION,
    RequirementKind,
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
        kind=RequirementKind.FUNCTIONAL,
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


# ---- v0.2.0: SE rigor + version compatibility ----

def test_intent_model_carries_classified_stakeholder_needs():
    from vmodel_contracts import IntentModel, IntentNeed, RequirementKind

    m = IntentModel(
        session_id="s", problem_statement="p", target_users=["u"],
        core_value_proposition="v",
        stakeholder_needs=[
            IntentNeed(need_id="SN-1", statement="Founders need specs before code", kind=RequirementKind.FUNCTIONAL, source_turns=[2]),
            IntentNeed(need_id="SN-2", statement="Founder data must stay secure", kind=RequirementKind.NON_FUNCTIONAL, source_turns=[12]),
        ],
        in_scope=["interviews"], out_of_scope=["codegen"], source_turns={},
    )
    kinds = {n.need_id: n.kind for n in m.stakeholder_needs}
    assert kinds == {"SN-1": RequirementKind.FUNCTIONAL, "SN-2": RequirementKind.NON_FUNCTIONAL}


def test_intent_model_requires_at_least_one_need():
    import pytest
    from pydantic import ValidationError

    from vmodel_contracts import IntentModel

    with pytest.raises(ValidationError):
        IntentModel(session_id="s", problem_statement="p", target_users=["u"],
                    core_value_proposition="v", stakeholder_needs=[],
                    in_scope=["x"], out_of_scope=["y"], source_turns={})


def test_version_check_rejects_wrong_minor_loudly():
    import pytest

    from vmodel_contracts import ContractVersionMismatch, check_compatible

    check_compatible({"contract_version": CONTRACT_VERSION})  # same: fine
    check_compatible({"contract_version": CONTRACT_VERSION + ".1"})  # patch drift: fine
    with pytest.raises(ContractVersionMismatch) as ei:
        check_compatible({"contract_version": "0.1.0"})
    assert "0.1.0" in str(ei.value)
    with pytest.raises(ContractVersionMismatch):
        check_compatible({})  # pre-versioning payload


def test_requirement_kind_round_trip():
    from vmodel_contracts import RequirementKind

    r = Requirement(requirement_id="R-2", title="Data encrypted", statement="User data shall be encrypted at rest.",
                    priority=Priority.MUST, kind=RequirementKind.NON_FUNCTIONAL,
                    acceptance=[AcceptanceCriterion(criterion_id="AC-1", statement="AES-256 at rest")],
                    need_ids=["N-1"], intent_fields=["stakeholder_needs"])
    assert Requirement.model_validate(r.model_dump(mode="json")).kind == RequirementKind.NON_FUNCTIONAL


def test_intent_model_carries_assumptions_v030():
    from vmodel_contracts import IntentModel, IntentNeed, RequirementKind

    m = IntentModel(
        session_id="s", problem_statement="p", target_users=["u"], core_value_proposition="v",
        stakeholder_needs=[IntentNeed(need_id="SN-1", statement="x", kind=RequirementKind.FUNCTIONAL)],
        in_scope=["a"], out_of_scope=["b"],
        assumptions=["internal and external data cannot conflict"],
        source_turns={},
    )
    assert m.assumptions == ["internal and external data cannot conflict"]


def test_srs_document_roundtrip():
    from vmodel_contracts import Requirement, RequirementKind, SRSDocument
    r = Requirement(requirement_id="R-1", title="t", statement="The system shall x",
                    priority="must", kind=RequirementKind.FUNCTIONAL, need_ids=["SN-1"],
                    intent_fields=["stakeholder_needs"],
                    acceptance=[{"criterion_id": "AC-1", "statement": "observable outcome"}])
    srs = SRSDocument(session_id="s", intent_model_ref="s", purpose="p", scope_summary="sc",
                      definitions={"TMS": "transport mgmt"}, functional=[r], non_functional=[],
                      constraints=["c"], open_questions=["q"])
    assert srs.requirement_ids() == {"R-1"}
    assert srs.requirements() == [r]


def test_text_qa_guards_shared():
    from vmodel_contracts import text_qa
    assert text_qa.is_solution_language("GET /health returns 200")
    assert text_qa.is_solution_language("encrypted with AES-256")
    assert text_qa.names_technology("queued through Kafka")
    assert not text_qa.is_solution_language("exactly one alert within the refresh cycle")
    assert text_qa.grounded_in("surfer cancels a booking", ["surfers book lessons"])
    assert not text_qa.grounded_in("portfolio of case studies", ["surfers book lessons"])
