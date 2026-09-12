"""The shared price table (one table for every repo; ADR-0002 doctrine)."""
import json

import pytest

from vmodel_contracts import (PRICE_TABLE_VERSION, PRICES_USD_PER_MTOK,
                              load_price_table, price_for)


def test_local_models_are_free_however_the_provider_is_spelled():
    # 2026-09-12 crash: langchain reports model_provider 'chatollama' with a
    # bare model name ('phi4'); an exact-match check on 'ollama' missed it and
    # a $0 local call crashed as "unpriced".
    for provider in ("ollama", "chatollama", "Ollama", "ChatOllama"):
        assert price_for("phi4", provider) == (0.0, 0.0)
    assert price_for("ollama:phi4", "") == (0.0, 0.0)
    assert price_for("ollama/phi4", "") == (0.0, 0.0)


def test_priced_remote_models_come_from_the_table():
    for model, pair in PRICES_USD_PER_MTOK.items():
        assert price_for(model, "deepseek" if model.startswith("deepseek") else "openai") == pair


def test_unpriced_remote_call_crashes_loudly():
    # an unpriced PAID call is an unbudgeted call - never a silent $0
    with pytest.raises(KeyError, match="no price for 'some-new-paid-model'"):
        price_for("some-new-paid-model", "openai")


def test_operator_override_file_wins(tmp_path, monkeypatch):
    override = tmp_path / "prices.json"
    override.write_text(json.dumps({"gpt-5": [9.99, 99.9], "brand-new-model": [1.0, 2.0]}))
    monkeypatch.setenv("VMODEL_PRICE_TABLE", str(override))
    table = load_price_table()
    assert table["gpt-5"] == (9.99, 99.9)          # corrected price wins
    assert table["brand-new-model"] == (1.0, 2.0)  # new model without a release
    assert table["deepseek-flash"] == PRICES_USD_PER_MTOK["deepseek-flash"]  # untouched
    monkeypatch.delenv("VMODEL_PRICE_TABLE")
    assert load_price_table() == PRICES_USD_PER_MTOK


def test_table_is_versioned():
    assert PRICE_TABLE_VERSION and isinstance(PRICE_TABLE_VERSION, str)
