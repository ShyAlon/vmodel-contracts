from vmodel_contracts import DELEGATION_DOCTRINE, INTENT_GATE_RUBRIC, intent_gate_instructions


def test_canonical_rubric_distinguishes_recorded_gaps_from_intent_defects():
    text=intent_gate_instructions()
    assert text.count(DELEGATION_DOCTRINE) == 1 and text.count(INTENT_GATE_RUBRIC) == 1
    for engineering in ("APIs", "historical data sources", "cloud providers", "model-verification methods"):
        assert engineering in INTENT_GATE_RUBRIC
    assert "material ambiguity that is neither delegated nor declared" in INTENT_GATE_RUBRIC
    assert "Do NOT reject" in INTENT_GATE_RUBRIC
