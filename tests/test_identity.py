import pytest
from pydantic import ValidationError
from vmodel_contracts import ConOpsDocument, TechnologySelection, canonical_concept_id, normalize_identity

def test_boundary_normalization_and_alias_resolution():
    assert normalize_identity(" Progressive_Web App! ") == "progressive-web-app"
    assert canonical_concept_id("Progressive Web Application") == "concept:pwa"

def test_conops_ids_are_resolved_once_at_parse_boundary():
    p={"session_id":"s","stakeholder_context":[{"stakeholder":"u","role":"r","goals":["g"],"operating_environment":"e","source_turns":[1]}],"operational_scenarios":[{"scenario_id":"OS-1","name":"n","trigger":"t","actors":["u"],"operational_flow":["x"],"success_outcome":"y","source_turns":[1]}],"concept_options":[{"name":"PWA","summary":"s","advantages":["a"],"disadvantages":["d"]},{"name":"Native app","summary":"s","advantages":["a"],"disadvantages":["d"]}],"decision":{"selected_concept":"PWA","rationale":"r","founder_confirmed":True,"source_turns":[1]}}
    d=ConOpsDocument.model_validate(p)
    assert d.decision.selected_concept_id == "concept:pwa"
    assert d.concept_options[0].concept_id == "concept:pwa"

def test_off_list_requires_structured_justification():
    with pytest.raises(ValidationError, match="off_list_justification"):
        TechnologySelection(slot_id="slot:runtime", technology_id="off-list:rare", display_name="Rare")

def test_stack_entry_dispositions_require_content_and_remain_non_executable():
    from vmodel_contracts import ArchitectureOverview
    base = {"session_id":"s", "stack_entries":[], "components":[], "decisions":[], "non_functionals":{}}
    research = ArchitectureOverview.model_validate({**base, "stack_entry_dispositions":[
        {"key":"real_time_data_source", "status":"research_required", "research_brief":"Find current APIs, terms, and coverage."}]})
    assert research.stack_entries == []
    assert research.stack_entry_dispositions[0].research_brief.startswith("Find")
    excluded = ArchitectureOverview.model_validate({**base, "stack_entry_dispositions":[
        {"key":"database", "status":"not_applicable", "reason":"The stateless concept stores no data."}]})
    assert excluded.stack_entries == []
    for item in ({"key":"x", "status":"research_required"}, {"key":"x", "status":"not_applicable"}):
        with pytest.raises(ValidationError):
            ArchitectureOverview.model_validate({**base, "stack_entry_dispositions":[item]})
