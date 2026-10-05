import pytest
from pydantic import ValidationError
from vmodel_contracts import BaselineMode, RepositoryManifest, SystemBaseline


def repo(name="spec-generator"):
    return RepositoryManifest(name=name, languages=["Python"], module_entry_points=["spec_generator.cli"],
                              runtime=["Python 3.10+", "Ollama"], persistence=["SQLite checkpoints"],
                              existing_contracts=["IntentModel -> SpecBundle"])


def test_existing_baseline_round_trip_and_version_stamp():
    b = SystemBaseline(baseline_id="vmodel-six-repos-2026-09", system_name="V-model", mode="existing",
                       repositories=[repo()], immutable_decisions=["Modules exchange only vmodel-contracts payloads"])
    assert b.mode is BaselineMode.EXISTING
    assert b.repositories[0].contract_version == "0.22.0"
    assert SystemBaseline.model_validate_json(b.model_dump_json()) == b


def test_greenfield_is_explicit_and_empty():
    b = SystemBaseline(baseline_id="new-product", system_name="New product", mode="greenfield")
    assert b.repositories == []
    with pytest.raises(ValidationError, match="greenfield baseline"):
        SystemBaseline(baseline_id="bad", system_name="Bad", mode="greenfield", repositories=[repo()])


def test_existing_cannot_be_an_empty_implicit_archetype():
    with pytest.raises(ValidationError, match="at least one repository"):
        SystemBaseline(baseline_id="bad", system_name="Bad", mode="existing")


def test_migrate_restamps_system_baseline(tmp_path, capsys):
    import json

    from vmodel_contracts import CONTRACT_VERSION, check_compatible
    from vmodel_contracts.migrate import migrate_file

    path = tmp_path / "greenfield-baseline.json"
    path.write_text(json.dumps({
        "contract_version": "0.13.0",
        "baseline_version": "1.0",
        "baseline_id": "greenfield-old-session",
        "system_name": "Greenfield product (old interview session)",
        "mode": "greenfield",
        "repositories": [],
        "immutable_decisions": [],
    }))

    assert migrate_file(path) == 0
    migrated = json.loads(path.read_text())
    assert migrated["contract_version"] == CONTRACT_VERSION
    check_compatible(migrated)
    assert "SystemBaseline" in capsys.readouterr().out
