

def test_missing_execution_normalizes_to_empty_code_owned_container():
    from vmodel_contracts import TestDefinition
    d=TestDefinition.model_validate({"preconditions":[],"steps":["invoke port"],
      "expected_outcomes":["escalation sent"],"cleanup":[],"cases":[]})
    assert d.execution.model_dump(exclude={"contract_version"},exclude_none=True)=={}


def test_test_execution_has_no_selector_field():
    # Selectors are the developer's, bound at implementation time. A spec-time
    # selector is imagined implementation, so the contract refuses the key.
    import pytest
    from pydantic import ValidationError
    from vmodel_contracts.verification import TestExecution

    with pytest.raises(ValidationError):
        TestExecution(selector="#score")
    assert TestExecution(url="/health", method="GET", expected_status=200).url == "/health"


def _vitem(**kw):
    base = dict(validation_id="V-1", need_ids=["N-1"], what_the_human_does="Hand the app to a 7-year-old.",
                what_to_observe="Whether the child treats it as a game.", pass_when="Most testers call it game-like.",
                evidence="Observation note", environment="physical iPad")
    return {**base, **kw}


def test_validation_item_requires_a_need_and_the_criterion_is_optional():
    import pytest
    from pydantic import ValidationError
    from vmodel_contracts.verification import ValidationItem

    item = ValidationItem(**_vitem())
    assert item.criterion_id is None and item.verified_by == [] and item.components == []
    with pytest.raises(ValidationError):
        ValidationItem(**_vitem(need_ids=[]))
    bad = _vitem()
    del bad["need_ids"]
    with pytest.raises(ValidationError):
        ValidationItem(**bad)
    assert ValidationItem(**_vitem(criterion_id="AC-4", verified_by=["T-9"])).verified_by == ["T-9"]


def test_validation_plan_refuses_duplicate_ids():
    import pytest
    from pydantic import ValidationError
    from vmodel_contracts.verification import ValidationPlan

    ValidationPlan(session_id="s", items=[_vitem(), _vitem(validation_id="V-2")])
    with pytest.raises(ValidationError, match="duplicate validation_id: V-1"):
        ValidationPlan(session_id="s", items=[_vitem(), _vitem()])


def _test(**kw):
    base = dict(test_id="T-1", level="acceptance", criterion_id="AC-1", description="d", runner="http",
                components=["Progress Store"],
                definition={"preconditions": [], "steps": [], "expected_outcomes": [], "cleanup": [], "cases": [], "execution": {}})
    return {**base, **kw}


def test_acceptance_test_requires_components():
    import pytest
    from pydantic import ValidationError
    from vmodel_contracts.verification import AcceptanceTest

    assert AcceptanceTest(**_test()).components == ["Progress Store"]
    with pytest.raises(ValidationError):
        AcceptanceTest(**_test(components=[]))
    gone = _test()
    del gone["components"]
    with pytest.raises(ValidationError):
        AcceptanceTest(**gone)


def test_runner_description_lists_no_semantic():
    from vmodel_contracts.verification import AcceptanceTest

    desc = AcceptanceTest.model_fields["runner"].description
    assert "semantic" not in desc and "'ui'" in desc
