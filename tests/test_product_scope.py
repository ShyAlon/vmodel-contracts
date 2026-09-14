from vmodel_contracts import (PRODUCT_SCOPE_DEFINITION, SCOPE_DECLINE_PREFIX,
                              SCOPE_IN_SIGNALS, SCOPE_OUT_SIGNALS)


def test_canonical_scope_wording_and_signal_data():
    assert PRODUCT_SCOPE_DEFINITION == "interactive applications - including games - delivered on web or mobile platforms"
    assert PRODUCT_SCOPE_DEFINITION in SCOPE_DECLINE_PREFIX
    assert any("game" in pattern for pattern, _ in SCOPE_IN_SIGNALS)
    assert any("mobile" in pattern for pattern, _ in SCOPE_IN_SIGNALS)
    assert any("bakery" in pattern for pattern, _ in SCOPE_OUT_SIGNALS)
