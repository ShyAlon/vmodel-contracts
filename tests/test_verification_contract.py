

def test_missing_execution_normalizes_to_empty_code_owned_container():
    from vmodel_contracts import TestDefinition
    d=TestDefinition.model_validate({"preconditions":[],"steps":["invoke port"],
      "expected_outcomes":["escalation sent"],"cleanup":[],"cases":[]})
    assert d.execution.model_dump(exclude={"contract_version"},exclude_none=True)=={}
