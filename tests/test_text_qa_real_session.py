"""Regression from a real run (Duolingo Music PWA session): the SRS lint flagged ordinary Title Case
title words and a latency number. The corpus is the founder's real intent model plus his concept of
operations. The requirement texts mirror the flagged items from that run (reconstructed from the
review output, not the original SRS file)."""
import json
from pathlib import Path

from vmodel_contracts.text_qa import srs_draft_findings

FIX = Path(__file__).parent / "fixtures"
CORPUS = json.dumps(json.loads((FIX / "duolingo_intent_model.json").read_text())) + \
    json.dumps(json.loads((FIX / "duolingo_conops.json").read_text()))

DRAFT = {"functional": [
    {"requirement_id": "R-2", "title": "No User Management Required",
     "statement": "The application shall operate without requiring user management, including accounts, login, or profiles.", "acceptance": []},
    {"requirement_id": "R-15", "title": "Exercise Retry and Switching Capability",
     "statement": "The app shall allow the user to retry an exercise indefinitely or switch to another exercise.", "acceptance": []},
    {"requirement_id": "R-4", "title": "Cross-Platform Compatibility",
     "statement": "The application shall be fully functional on both iPhone and iPad devices.", "acceptance": []},
    {"requirement_id": "R-10", "title": "Self-Contained Application Operation",
     "statement": "The application shall operate independently without requiring external data sources during runtime.", "acceptance": []},
    {"requirement_id": "R-11", "title": "Performance and Responsiveness",
     "statement": "The application shall maintain a responsive user interface with minimal lag during interactions.",
     "acceptance": [{"criterion_id": "AC-11.1", "statement": "Each tap is acknowledged within 200 ms."}]},
], "non_functional": []}


def found(findings, rid=None):
    return {(f["location"].split()[0], f["rule"], f["span"]) for f in findings if rid in (None, f["location"].split()[0])}


def test_title_case_words_are_not_inventions():
    assert found(srs_draft_findings(DRAFT, CORPUS), "R-2") == set()
    spans = {s for _, _, s in found(srs_draft_findings(DRAFT, CORPUS))}
    assert not spans & {"Required", "Capability", "Cross-Platform", "Compatibility", "Application", "Responsiveness"}


def test_latency_number_is_an_invention_signal_not_an_http_status():
    got = found(srs_draft_findings(DRAFT, CORPUS), "R-11")
    assert ("R-11", "absent_from_interview", "200") in got
    assert not any(rule == "http_status" for _, rule, _ in got)


def test_real_flagged_set_collapses_to_the_one_real_signal():
    assert found(srs_draft_findings(DRAFT, CORPUS)) == {("R-11", "absent_from_interview", "200")}


def test_needs_and_conops_text_count_as_interview_evidence():
    d = {"functional": [{"requirement_id": "R-1", "title": "t", "statement": "The system shall show Pitchfork charts.", "acceptance": []}], "non_functional": []}
    assert srs_draft_findings(d, "intent only")
    assert not srs_draft_findings(d, "intent only " + "pitchfork in the concept of operations")


def test_numbers_match_whole_numbers_only():
    d = {"functional": [{"requirement_id": "R-1", "title": "t", "statement": "The system shall respond within 200 ms.", "acceptance": []}], "non_functional": []}
    assert srs_draft_findings(d, "Duolingo Clone 2000")           # 200 is not inside 2000
    assert not srs_draft_findings(d, "answer within 200 ms")


def test_http_status_still_fires_with_http_context():
    for text in ("The system shall return HTTP 404 when missing.", "The system shall respond with 201 on create.",
                 "The system shall reply 401 Unauthorized.", "The API returns 500 for errors."):
        d = {"functional": [{"requirement_id": "R-1", "title": "t", "statement": text, "acceptance": []}], "non_functional": []}
        assert "http_status" in {f["rule"] for f in srs_draft_findings(d, "")}, text
    d = {"functional": [{"requirement_id": "R-1", "title": "t", "statement": "The system shall load in under 300 seconds.", "acceptance": []}], "non_functional": []}
    assert "http_status" not in {f["rule"] for f in srs_draft_findings(d, "")}


def test_acronyms_camelcase_and_midsentence_names_in_titles_and_text_still_flag():
    d = {"functional": [{"requirement_id": "R-1", "title": "Export to PDF and FooBar",
                         "statement": "The system shall sync with Dropbox.", "acceptance": []}], "non_functional": []}
    spans = {f["span"] for f in srs_draft_findings(d, "nothing relevant")}
    assert {"PDF", "FooBar"} <= spans and "Dropbox" in spans
