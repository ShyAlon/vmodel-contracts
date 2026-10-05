

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
