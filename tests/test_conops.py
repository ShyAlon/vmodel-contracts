import pytest
from pydantic import ValidationError

from vmodel_contracts import CONTRACT_VERSION, ConOpsDocument


def _payload():
    return {
        "session_id": "s1",
        "stakeholder_context": [{
            "stakeholder": "habit tracker", "role": "records daily progress",
            "goals": ["log in seconds"], "operating_environment": "on a phone while moving",
            "source_turns": [3],
        }],
        "operational_scenarios": [{
            "scenario_id": "OS-1", "name": "Log progress", "trigger": "habit completed",
            "actors": ["habit tracker"], "operational_flow": ["open product", "record points"],
            "success_outcome": "points persist across devices", "exceptions": ["offline"],
            "source_turns": [4, 5],
        }],
        "concept_options": [
            {"name": "Native app", "summary": "installed mobile product",
             "advantages": ["native APIs"], "disadvantages": ["store distribution"]},
            {"name": "PWA", "summary": "installable web product",
             "advantages": ["one web deployment"], "disadvantages": ["limited background APIs"]},
        ],
        "decision": {"selected_concept": "Native app", "rationale": "reliable native health access",
                     "founder_confirmed": True, "source_turns": [9]},
    }


def test_conops_round_trip_and_version_stamp():
    doc = ConOpsDocument.model_validate(_payload())
    assert doc.contract_version == CONTRACT_VERSION == "0.14.0"
    assert doc.decision.selected_concept == "Native app"
    assert ConOpsDocument.model_validate(doc.model_dump()).operational_scenarios[0].scenario_id == "OS-1"


def test_conops_requires_explicit_founder_decision():
    p = _payload(); p["decision"]["founder_confirmed"] = False
    with pytest.raises(ValidationError, match="founder-confirmed"):
        ConOpsDocument.model_validate(p)


def test_conops_decision_must_select_compared_option():
    p = _payload(); p["decision"]["selected_concept"] = "Desktop client"
    with pytest.raises(ValidationError, match="concept_options"):
        ConOpsDocument.model_validate(p)


def test_conops_needs_real_comparison_and_unique_scenarios():
    p = _payload(); p["concept_options"] = p["concept_options"][:1]
    with pytest.raises(ValidationError): ConOpsDocument.model_validate(p)
    p = _payload(); p["operational_scenarios"].append(dict(p["operational_scenarios"][0]))
    with pytest.raises(ValidationError, match="scenario ids"):
        ConOpsDocument.model_validate(p)
