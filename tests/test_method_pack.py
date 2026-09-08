"""The method pack is prompt context on a 14B: the size cap is the contract."""
from vmodel_contracts.method_pack import METHOD_PACK_TOKEN_CAP, load_method_pack

REQUIRED_SECTIONS = [
    "NFR taxonomy",
    "Elicitation discipline",
    "Well-formed requirements",
    "Conflict and scope",
]


def test_pack_stays_under_token_cap():
    pack = load_method_pack()
    estimated_tokens = len(pack) / 4
    assert estimated_tokens <= METHOD_PACK_TOKEN_CAP, (
        f"method pack grew to ~{int(estimated_tokens)} tokens (cap {METHOD_PACK_TOKEN_CAP}); "
        "prompt context on a local 14B is the scarce resource - trim, don't grow"
    )


def test_pack_has_required_sections_and_attribution():
    pack = load_method_pack()
    for section in REQUIRED_SECTIONS:
        assert section in pack, f"missing section: {section}"
    assert "SWEBOK" in pack and "computer.org/swebok" in pack, "attribution line missing"


def test_pack_shapes_questions_never_answers():
    assert "never becomes a need" in load_method_pack()


def test_sectioned_loading():
    from vmodel_contracts.method_pack import load_method_pack
    slice_ = load_method_pack(["1", "2"])
    assert "Elicitation discipline" in slice_
    assert "Well-formed requirements" not in slice_
    full = load_method_pack()
    for n in "12345":
        assert load_method_pack([n])
    assert len(slice_) < len(full)
    import pytest
    with pytest.raises(ValueError, match="unknown method-pack section"):
        load_method_pack(["9"])
