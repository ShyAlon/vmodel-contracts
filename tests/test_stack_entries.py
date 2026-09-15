"""0.13.0: typed stack entries replace the parallel maps.

The pre-0.13.0 shape (`stack` + `stack_baseline_refs`) asked the model to keep
two free-form maps perfectly key-synchronized - a relation JSON-schema grammar
cannot enforce (2026-09-11 phi4 live failure: a schema-legal bogus
`stack_baseline_refs` string key inside the `stack` map, and the two maps' key
sets disagreed). Co-locating key/value/refs in one typed record makes that
misplacement structurally impossible; ambiguous legacy payloads refuse to heal
rather than being guessed.
"""
import json

import pytest
from pydantic import ValidationError

from vmodel_contracts import ArchitectureOverview, CONTRACT_VERSION, StackEntry
from vmodel_contracts.migrate import migrate_file


def _entry(**over):
    base = {"key": "language", "value": "Python 3.14", "technology_id":"tech:python", "decision_id":"ADR-1",
            "baseline_refs": ["runtime:spec-generator:1"], "migration_adr_id": None}
    return {**base, **over}


def _overview(**over):
    base = {"session_id": "s", "baseline_id": "b",
            "stack_entries": [_entry()],
            "components": [], "decisions": [{"decision_id":"ADR-1","title":"Language","decision":"Python","rationale":"fit","driver":"simplicity","options_considered":[],"executes_concept_ids":[],"technology_selections":[{"slot_id":"slot:language","technology_id":"tech:python","display_name":"Python 3.14","baseline_refs":["runtime:spec-generator:1"]}]}], "non_functionals": {}}
    return {**base, **over}


def test_stack_entry_shape_is_enforced():
    e = StackEntry.model_validate(_entry())
    assert e.key == "language" and e.migration_adr_id is None
    with pytest.raises(ValidationError):
        StackEntry.model_validate(_entry(key=""))
    with pytest.raises(ValidationError):
        StackEntry.model_validate(_entry(value=""))
    with pytest.raises(ValidationError):
        StackEntry.model_validate(_entry(migration_adr_id="ADR1"))  # not the id shape
    ok = StackEntry.model_validate(_entry(baseline_refs=[], migration_adr_id="ADR-2"))
    assert ok.migration_adr_id == "ADR-2"


def test_overview_requires_typed_entries_and_rejects_the_parallel_maps():
    ArchitectureOverview.model_validate(_overview())
    with pytest.raises(ValidationError):  # the old shape is gone
        ArchitectureOverview.model_validate(_overview(stack={"language": "Python"}))
    with pytest.raises(ValidationError):  # an entry is a record, not a bare string
        ArchitectureOverview.model_validate(
            _overview(stack_entries=[{"language": "Python"}]))


def test_migrate_refuses_pre_identity_stack_shapes(tmp_path):
    payload={"contract_version":"0.12.0","session_id":"s","baseline_id":"b","stack":{"language":"Python"},"components":[],"decisions":[],"non_functionals":{}}
    p=tmp_path/"architecture.json";p.write_text(json.dumps(payload));before=p.read_text()
    assert migrate_file(p)==1
    # migration is transactional: semantic identity/ADR ownership is never invented
    assert p.read_text()==before


def test_migrate_refuses_the_phi4_failure_shape(tmp_path):
    # The exact 2026-09-11 failure CLASS: the model dropped a bogus
    # `stack_baseline_refs` key inside the free-form stack map, and the two
    # maps' key sets disagree. No honest co-location exists; refuse loudly.
    # (Byte-exact regression fixture lands when the raw completion is captured
    # via SPEC_GENERATOR_LOG_RAW=1 - the raw output was not logged in that run;
    # this fixture is a faithful reproduction of the error's own description,
    # not the original bytes.)
    payload = {"contract_version": "0.12.0", "session_id": "s", "baseline_id": "b",
               "stack": {"language": "Python", "stack_baseline_refs": "language"},
               "stack_baseline_refs": {"language": ["runtime:spec-generator:1"]},
               "components": [], "decisions": [], "non_functionals": {}}
    p = tmp_path / "architecture.json"
    p.write_text(json.dumps(payload))
    assert migrate_file(p) == 1
    out = json.loads(p.read_text())
    assert "stack" in out and "stack_entries" not in out  # untouched - no partial heal


def test_migrate_refuses_malformed_entry_values(tmp_path):
    payload = {"contract_version": "0.12.0", "session_id": "s", "baseline_id": "b",
               "stack": {"language": ["Python"]},
               "stack_baseline_refs": {"language": ["runtime:spec-generator:1"]},
               "components": [], "decisions": [], "non_functionals": {}}
    p = tmp_path / "architecture.json"
    p.write_text(json.dumps(payload))
    assert migrate_file(p) == 1
