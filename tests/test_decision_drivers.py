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


def test_migrate_synthesizes_legacy_decision(tmp_path):
    payload = {"contract_version": "0.7.0", "session_id": "s1",
               "stack": {"framework": "React"},
               "components": [{"contract_version": "0.7.0", "name": "web", "responsibility": "UI",
                               "requirement_ids": ["R-1"]}],
               "decisions": [{"contract_version": "0.7.0", "decision_id": "ADR-1", "title": "Frontend",
                              "decision": "React", "rationale": "biggest ecosystem",
                              "rejected": ["Angular - ceremony"]}],
               "non_functionals": {}}
    p = tmp_path / "architecture.json"
    p.write_text(json.dumps(payload))
    assert migrate_file(p) == 0
    out = json.loads(p.read_text())
    dec = out["decisions"][0]
    assert dec["driver"] is None            # honest legacy form - no retroactive driver
    assert dec["options_considered"] == []
    assert dec["rejected"] == ["Angular - ceremony"]  # deprecated field carried
    assert out["contract_version"] == CONTRACT_VERSION
    ArchitectureOverview.model_validate(out)  # the migrated artifact validates
