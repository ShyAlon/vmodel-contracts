import pytest
from vmodel_contracts.architecture import StackEntryDisposition, TechnicalChoiceFraming, technical_choice_data

FRAMING = {"title": "Storing Your Data", "purpose": "Keeps the product's records between visits.", "default_value": "SQLite", "reason": "A single local user needs a small store.", "requirement_ids": ["R-1"], "options": [{"value": "SQLite", "label": "One Local Store", "implication": "Simple to run; a shared server may be needed later."}, {"value": "PostgreSQL", "label": "A Shared Store", "implication": "Supports shared access but adds a server to manage."}], "provenance": "design_proposal", "research_status": "pending"}

def test_explicit_default_requires_real_option_and_requirements():
    assert technical_choice_data(FRAMING, ["R-1"])["default_value"] == "SQLite"
    for value in ({**FRAMING, "default_value": "Redis"}, {**FRAMING, "reason": " "}, {**FRAMING, "research_status": "verified"}):
        with pytest.raises(ValueError): TechnicalChoiceFraming.model_validate(value)
    with pytest.raises(ValueError): technical_choice_data(FRAMING, ["R-2"])

def test_old_candidates_do_not_become_default_and_system_selection_must_match():
    base = {"key":"database", "status":"research_required", "research_brief":"Check docs", "candidate_options":["SQLite","PostgreSQL"]}
    assert StackEntryDisposition.model_validate(base).technical_choice is None
    with pytest.raises(ValueError): StackEntryDisposition.model_validate({**base, "technical_choice":FRAMING, "system_selection":{"value":"PostgreSQL"}})
    StackEntryDisposition.model_validate({**base, "technical_choice":FRAMING, "system_selection":{"value":"SQLite"}})

def test_override_reason_optional_no_fake_reason():
    value = StackEntryDisposition.model_validate({"key":"db", "status":"research_required", "research_brief":"check", "founder_decision":{"text":"Custom", "actor":"founder", "at":"t"}})
    assert value.founder_decision.reason == ""
