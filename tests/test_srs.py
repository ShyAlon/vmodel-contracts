

def test_design_constraint_requires_interview_provenance():
    import pytest
    from pydantic import ValidationError
    from vmodel_contracts import DesignConstraint
    traced=DesignConstraint(constraint_id="DC-1",statement="Use the mandated identity provider",source_turns=[7])
    assert traced.source_field == "constraints"
    with pytest.raises(ValidationError):
        DesignConstraint(constraint_id="DC-2",statement="Use AES-256",source_turns=[])
