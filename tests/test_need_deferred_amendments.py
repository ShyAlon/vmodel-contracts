"""Additive fields: IntentNeed.deferred, IntentNeed.amendment_id, IntentModel.amendments.
No contract version bump: old payloads must still parse and round-trip."""
import pytest
from pydantic import ValidationError
from vmodel_contracts import CONTRACT_VERSION, FounderAmendment, IntentModel, IntentNeed


def _intent(**over):
    base = dict(session_id="s", problem_statement="p", target_users=["u"], core_value_proposition="v",
                stakeholder_needs=[{"need_id": "SN-1", "statement": "x", "kind": "functional"}],
                in_scope=["a"], out_of_scope=["b"], source_turns={})
    base.update(over)
    return IntentModel(**base)


def test_old_payload_without_new_fields_parses_with_defaults():
    old = {"session_id": "s", "problem_statement": "p", "target_users": ["u"], "core_value_proposition": "v",
           "stakeholder_needs": [{"need_id": "SN-1", "statement": "x", "kind": "functional", "source_turns": [2]}],
           "in_scope": [], "out_of_scope": [], "source_turns": {}}
    im = IntentModel.model_validate(old)
    assert im.amendments == []
    n = im.stakeholder_needs[0]
    assert n.deferred is False and n.amendment_id is None


def test_old_payload_roundtrip_is_stable():
    im = _intent()
    again = IntentModel.model_validate_json(im.model_dump_json())
    assert again == im


def test_deferred_roundtrip():
    n = IntentNeed(need_id="SN-2", statement="later", kind="functional", deferred=True)
    assert IntentNeed.model_validate(n.model_dump()).deferred is True


def test_amendment_need_may_have_empty_source_turns():
    im = _intent(
        amendments=[{"amendment_id": "AM-1", "statement": "Use bundled songs", "decided_on": "2026-10-01",
                     "rationale": "legal"}],
        stakeholder_needs=[{"need_id": "SN-1", "statement": "Songs are bundled", "kind": "functional",
                            "amendment_id": "AM-1"}],
    )
    assert im.stakeholder_needs[0].source_turns == []
    assert im.amendments[0].source == "founder-channel"


def test_need_citing_unknown_amendment_rejected():
    with pytest.raises(ValidationError, match="unknown amendment"):
        _intent(stakeholder_needs=[{"need_id": "SN-1", "statement": "x", "kind": "functional",
                                    "amendment_id": "AM-9"}])


def test_amendment_id_shape_and_duplicates_rejected():
    with pytest.raises(ValidationError):
        FounderAmendment(amendment_id="A1", statement="s", decided_on="2026-10-01")
    a = {"amendment_id": "AM-1", "statement": "s", "decided_on": "2026-10-01"}
    with pytest.raises(ValidationError, match="duplicate"):
        _intent(amendments=[a, a])


def test_contract_version_not_bumped():
    assert CONTRACT_VERSION == "0.27.2"
