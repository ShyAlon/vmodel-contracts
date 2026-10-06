import pytest
from pydantic import ValidationError

from vmodel_contracts import FounderStackDecision, StackEntryDisposition, open_stack_decisions
from vmodel_contracts.architecture import ArchitectureOverview


def _slot(key, decision=None):
    return StackEntryDisposition(key=key, status="research_required", research_brief="Which one?", founder_decision=decision)


def _overview(dispositions):
    return ArchitectureOverview(session_id="s", stack_entries=[], stack_entry_dispositions=dispositions, components=[], decisions=[])


def test_old_disposition_without_decision_validates():
    assert _slot("database").founder_decision is None


def test_decided_slot_is_not_open():
    d = FounderStackDecision(text="SQLite", actor="founder", at="2026-10-06T12:00:00Z")
    ov = _overview([_slot("database", d), _slot("queue")])
    assert [x.key for x in open_stack_decisions(ov)] == ["queue"]


def test_blank_decision_rejected():
    with pytest.raises(ValidationError):
        FounderStackDecision(text="   ", actor="founder", at="2026-10-06T12:00:00Z")


def test_decision_not_allowed_on_not_applicable():
    d = FounderStackDecision(text="x", actor="founder", at="2026-10-06T12:00:00Z")
    with pytest.raises(ValidationError):
        StackEntryDisposition(key="cache", status="not_applicable", reason="none", founder_decision=d)
