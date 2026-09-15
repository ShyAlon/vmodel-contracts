"""ADR-0021 (0.8.0): decisions carry driver + options_considered; migrate
synthesizes the honest legacy form for pre-0.8.0 artifacts."""
import json

import pytest
from pydantic import ValidationError

from vmodel_contracts.architecture import (ArchitectureDecision, ArchitectureOverview,
                                           ConsideredOption, DecisionDriver)
from vmodel_contracts.migrate import migrate_file
from vmodel_contracts.version import CONTRACT_VERSION


def _decision(**kw):
    base = {"decision_id": "ADR-1", "title": "Frontend framework", "decision": "React",
            "rationale": "Largest ecosystem for this archetype.",
            "driver": "ecosystem_maturity",
            "options_considered": [{"option": "Angular", "reason": "More ceremony for a solo build."}]}
    base.update(kw)
    return base


def test_decision_with_driver_and_options_validates():
    d = ArchitectureDecision.model_validate(_decision())
    assert d.driver is DecisionDriver.ECOSYSTEM_MATURITY
    assert d.options_considered[0].option == "Angular"


def test_all_five_drivers_accepted():
    for v in ["founder_constraint", "ecosystem_maturity", "community_adoption", "team_fit", "simplicity"]:
        assert ArchitectureDecision.model_validate(_decision(driver=v)).driver.value == v


def test_unknown_driver_rejected():
    with pytest.raises(ValidationError):
        ArchitectureDecision.model_validate(_decision(driver="gut_feeling"))


def test_driver_and_options_required_present():
    for missing in ("driver", "options_considered"):
        bad = _decision()
        bad.pop(missing)
        with pytest.raises(ValidationError):
            ArchitectureDecision.model_validate(bad)


def test_no_options_floor_empty_list_is_valid():
    d = ArchitectureDecision.model_validate(_decision(driver="founder_constraint", options_considered=[]))
    assert d.options_considered == []


def test_migrate_refuses_pre_identity_architecture(tmp_path):
    payload={"contract_version":"0.7.0","session_id":"s","stack":{"framework":"React"},"components":[],"decisions":[],"non_functionals":{}}
    p=tmp_path/"architecture.json"; p.write_text(json.dumps(payload))
    before=p.read_text(); assert migrate_file(p)==1; assert p.read_text()==before
