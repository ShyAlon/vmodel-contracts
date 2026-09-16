import pytest
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


def _intent_payload(stamp):
    from vmodel_contracts import IntentModel
    p = IntentModel(session_id="s", problem_statement="p", target_users=["u"],
                    core_value_proposition="v", in_scope=["a"], out_of_scope=["b"],
                    stakeholder_needs=[{"need_id": "SN-1", "statement": "s", "kind": "functional",
                                        "source_turns": [0]}],
                    assumption_items=[{"statement": "a", "source_turns": [0]}],
                    scope_exclusions=[{"item": "x", "source_turns": [1], "explicit": True}],
                    source_turns={"problem_statement": [0]}).model_dump(mode="json")
    def _stamp(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "contract_version":
                    node[k] = stamp
                else:
                    _stamp(v)
        elif isinstance(node, list):
            for v in node:
                _stamp(v)
    _stamp(p)
    return p


def test_migrate_restamps_top_and_nested(tmp_path, capsys):
    import json
    from vmodel_contracts.migrate import migrate_file
    p = _intent_payload("0.5.0")
    f = tmp_path / "intent_model.json"
    f.write_text(json.dumps(p))
    assert migrate_file(f) == 0
    out = json.loads(f.read_text())
    from vmodel_contracts import CONTRACT_VERSION, check_compatible
    check_compatible(out)  # passes now
    assert out["stakeholder_needs"][0]["contract_version"] == CONTRACT_VERSION
    assert out["assumption_items"][0]["contract_version"] == CONTRACT_VERSION
    assert out["scope_exclusions"][0]["contract_version"] == CONTRACT_VERSION
    assert "0.5.0" in capsys.readouterr().out  # reports what it changed


def test_migrate_refuses_incompatible_payload(tmp_path, capsys):
    import json
    from vmodel_contracts.migrate import migrate_file
    p = _intent_payload("0.5.0")
    del p["problem_statement"]  # schema drift - a re-stamp would launder a bad payload
    f = tmp_path / "intent_model.json"
    f.write_text(json.dumps(p))
    assert migrate_file(f) == 1
    assert json.loads(f.read_text())["contract_version"] == "0.5.0", "refusal leaves the file untouched"
    assert "problem_statement" in capsys.readouterr().err


def test_migrate_noop_when_current(tmp_path, capsys):
    import json
    from vmodel_contracts import CONTRACT_VERSION
    from vmodel_contracts.migrate import migrate_file
    f = tmp_path / "intent_model.json"
    f.write_text(json.dumps(_intent_payload(CONTRACT_VERSION)))
    assert migrate_file(f) == 0
    assert "nothing to do" in capsys.readouterr().out



def test_test_definition_has_one_stable_shape_and_preserves_matrices():
    from pydantic import ValidationError
    from vmodel_contracts import TestDefinition

    d = TestDefinition(
        preconditions=["service is running"],
        steps=["POST /bookings with a valid request"],
        expected_outcomes=["HTTP 201 and the booking is persisted"],
        cleanup=["delete the booking"],
        cases=[
            {"name": "E-1", "inputs": ["valid booking"], "expected_outcomes": ["accepted"]},
            {"name": "E-2", "inputs": ["duplicate booking"], "expected_outcomes": ["rejected"]},
        ],
        execution={"url": "/bookings", "method": "POST", "expected_status": 201},
    )
    assert [c.name for c in d.cases] == ["E-1", "E-2"]
    with pytest.raises(ValidationError):
        TestDefinition.model_validate({"setup": [], "execution": [], "verification": []})


def test_empty_llm_response_detail_preserves_provider_envelope_not_messages():
    from vmodel_contracts.runtime import empty_llm_response_detail

    response = type("R", (), {
        "id": "msg_1", "content": "",
        "response_metadata": {"finish_reason": "stop", "provider": "deepseek"},
        "usage_metadata": {"input_tokens": 3, "output_tokens": 0},
        "additional_kwargs": {"reasoning_content": ""},
    })()
    detail = empty_llm_response_detail(response, lambda value: value.replace("deepseek", "masked"))
    assert detail["id"] == "msg_1"
    assert detail["response_metadata"]["provider"] == "masked"
    assert "messages" not in detail


def test_debug_http_client_captures_full_exchange_without_request_headers(tmp_path, monkeypatch):
    import json
    import httpx
    from vmodel_contracts.runtime import debug_http_client

    sink = tmp_path / "llm-calls.jsonl"
    monkeypatch.setenv("VMODEL_DEBUG_HTTP", "1")
    monkeypatch.setenv("VMODEL_LLM_LOG", str(sink))
    client = debug_http_client(mask=lambda text: text.replace("secret", "MASKED"))
    request = client.build_request("POST", "https://api.example.test/chat/completions",
                                   headers={"Authorization": "Bearer secret"},
                                   json={"model": "m", "messages": [{"role": "user", "content": "debug me"}]})
    response = httpx.Response(200, request=request, headers={"x-request-id": "req_1"},
                              json={"id": "resp_1", "choices": [{"finish_reason": "stop", "message": {"content": "", "reasoning_content": "why"}}], "usage": {"completion_tokens_details": {"reasoning_tokens": 4}}})
    for hook in client.event_hooks["request"]:
        hook(request)
    for hook in client.event_hooks["response"]:
        hook(response)
    row = json.loads((tmp_path / "debug-http.jsonl").read_text())
    assert row["request"]["messages"][0]["content"] == "debug me"
    assert row["response"]["status_code"] == 200
    assert row["response"]["headers"]["x-request-id"] == "req_1"
    assert row["response"]["body"]["choices"][0]["message"]["reasoning_content"] == "why"
    assert row["response"]["body"]["usage"]["completion_tokens_details"]["reasoning_tokens"] == 4
    assert "authorization" not in row["request"]
    assert "secret" not in (tmp_path / "debug-http.jsonl").read_text()


def test_list_string_normalizer_handles_live_conops_shape():
    from vmodel_contracts import ConceptOption
    from vmodel_contracts.normalize import normalize_list_string_fields

    payload = {"concept_id":"concept:agent", "name":"Agent", "summary":"Acts for garage",
               "advantages":[{"statement":"Fewer manual calls","source_turns":[12]}],
               "disadvantages":[{"text":"Insurer integration varies","source_turns":[12]}]}
    fixed = normalize_list_string_fields(payload, ConceptOption)
    assert fixed["advantages"] == ["Fewer manual calls"]
    assert fixed["disadvantages"] == ["Insurer integration varies"]
    assert ConceptOption.model_validate(fixed).advantages == ["Fewer manual calls"]


def test_list_string_normalizer_leaves_unknown_objects_to_fail_loudly():
    from vmodel_contracts import ConceptOption
    from vmodel_contracts.normalize import normalize_list_string_fields
    from pydantic import ValidationError

    payload={"concept_id":"concept:x","name":"x","summary":"x",
             "advantages":[{"source_turns":[12]}],"disadvantages":["risk"]}
    fixed=normalize_list_string_fields(payload,ConceptOption)
    with pytest.raises(ValidationError):
        ConceptOption.model_validate(fixed)
