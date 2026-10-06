from vmodel_contracts import IntentModel, Requirement, text_qa as t
from vmodel_contracts.interview import ReferenceKind, ReferenceName


def req(rid, title, statement, kind="functional", needs=None, acc=None):
    return {"requirement_id": rid, "title": title, "statement": statement, "kind": kind,
            "need_ids": needs or [f"N-{rid[2:]}"], "intent_fields": ["stakeholder_needs"], "source_turns": [],
            "acceptance": acc or [{"criterion_id": f"AC-{rid[2:]}", "statement": f"{rid} works"}]}


R16 = req("R-16", "Bundled Lesson Content and Free Backing Tunes",
          "The app shall ship with all lesson content and all backing tunes already included in the delivered app, "
          "so that every lesson is fully usable without retrieving any content or audio from outside the app.")
R17 = req("R-17", "Bundled Lesson Content and Audio",
          "The app shall make all lesson content and all audio assets available to the child without retrieving "
          "any of them from an external source at runtime.")
R3 = req("R-3", "Local persistence of all progress data",
         "All data the app keeps about a child's progress shall be stored in the browser's local storage on the device.")
R18 = req("R-18", "Persistence of all progress data across app sessions",
          "The app shall retain all progress data so that when the child closes the app and reopens it, every value is present.")
CLEAN = req("R-9", "Parent Report", "The app shall show a parent a weekly summary of completed lessons.")


def test_known_real_pairs_land_in_review_band():
    """Real requirements from a founder session (calibration data, 2026-10-06)."""
    import json, pathlib
    rs = json.loads((pathlib.Path(__file__).parent / "fixtures" / "real_session_requirements.json").read_text())
    out = t.duplicate_requirement_pairs(rs)
    pairs = {frozenset((p["a"], p["b"])) for p in out["review"]}
    assert {"R-16", "R-17"} in [set(p) for p in pairs] and {"R-3", "R-18"} in [set(p) for p in pairs]
    assert out["merge"] == [] and not any("R-9" in p for p in pairs) and len(pairs) == 5
    assert t.REQ_REVIEW_THRESHOLD < 0.43 and t.REQ_MERGE_THRESHOLD == 0.90


def test_uncomparable_is_reported_not_passed():
    out = t.duplicate_requirement_pairs([R3, req("R-4", "", "")])
    assert out["uncomparable"] == ["R-4"]
    assert t.requirement_similarity(R3, req("R-4", "", "")) is None


def test_auto_merge_unions_and_records_provenance():
    a = req("R-1", "Offline Lessons", "The app shall deliver lessons offline.", needs=["N-1"],
            acc=[{"criterion_id": "AC-1", "statement": "Lessons open offline"}])
    b = req("R-2", "Offline Lessons", "The app shall deliver lessons offline.", needs=["N-2"],
            acc=[{"criterion_id": "AC-2", "statement": "lessons  open offline"}, {"criterion_id": "AC-3", "statement": "Audio plays offline"}])
    snapshot = repr([a, b])
    merged, merges = t.merge_duplicate_requirements([a, b, CLEAN])
    assert repr([a, b]) == snapshot
    assert [r["requirement_id"] for r in merged] == ["R-1", "R-9"]
    s = merged[0]
    assert s["need_ids"] == ["N-1", "N-2"]
    assert [c["criterion_id"] for c in s["acceptance"]] == ["AC-1", "AC-3"]
    assert s["merged_from"][0]["requirement_id"] == "R-2" and s["merged_from"][0]["score"] == 1.0
    assert merges[0]["survivor"] == "R-1"
    Requirement.model_validate({**s, "priority": "must"})  # provenance fits the contract


def test_no_merge_across_kinds():
    a = req("R-1", "Offline Lessons", "The app shall deliver lessons offline.")
    b = req("R-2", "Offline Lessons", "The app shall deliver lessons offline.", kind="non_functional")
    merged, merges = t.merge_duplicate_requirements([a, b])
    assert len(merged) == 2 and merges == []


def test_turn_tags():
    assert [f["span"] for f in t.turn_tag_findings("Kids learn (turn 2) and [Turn 3-4].")] == ["(turn 2)", "[Turn 3-4]"]
    assert t.turn_tag_findings("The child turns the page; turn 2 of the lesson") == []


def test_reference_names_whole_word_case_insensitive():
    f = t.reference_name_findings("Like duolingo 16k, the app. Duolingo 16Kids is different.", ["Duolingo 16K"], "R-1")
    assert [x["span"] for x in f] == ["duolingo 16k"] and f[0]["location"] == "R-1"
    assert t.reference_name_findings("nothing here", ["", "  ", "--"]) == []


def test_intent_model_reference_names_default_empty_and_roundtrip():
    f = IntentModel.model_fields["reference_names"]
    assert f.default_factory() == []
    n = ReferenceName(name="Duolingo 16K", kind=ReferenceKind.WORKING_TITLE, source_turns=[1])
    assert n.model_dump(mode="json")["kind"] == "working_title"
