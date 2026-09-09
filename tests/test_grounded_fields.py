"""0.4.0: grounded assumptions, provenance-carried exclusions, done-criteria, ops concepts."""
import pytest
from pydantic import ValidationError
from vmodel_contracts import Assumption, IntentModel, ScopeExclusion


def _intent(**over):
    base = dict(session_id="s", problem_statement="p", target_users=["u"],
                core_value_proposition="v",
                stakeholder_needs=[{"need_id": "SN-1", "statement": "x", "kind": "functional"}],
                in_scope=["a"], out_of_scope=["b"], source_turns={})
    base.update(over)
    return IntentModel(**base)


def test_assumption_requires_turns():
    with pytest.raises(ValidationError):
        Assumption(statement="invented", source_turns=[])


def test_grounded_fields_roundtrip():
    im = _intent(
        assumption_items=[{"statement": "sources never disagree", "source_turns": [6]}],
        scope_exclusions=[{"item": "mobile", "source_turns": [4], "explicit": True},
                          {"item": "on-prem", "explicit": False}],
        done_criteria=["customer onboarded unaided"],
        operational_concepts=["support team backed by R&D handles failures"],
    )
    assert im.assumption_items[0].source_turns == [6]
    assert im.scope_exclusions[1].explicit is False
    assert im.done_criteria and im.operational_concepts


def test_old_0_3_payloads_still_parse():
    im = _intent(assumptions=["legacy flat assumption"])
    assert im.assumptions == ["legacy flat assumption"]
    assert im.assumption_items == []


def test_glossary_roundtrip():
    im = _intent(glossary={"exceptions": "plan deviations the founder acts on"})
    assert im.glossary["exceptions"].startswith("plan")
    assert _intent().glossary == {}
