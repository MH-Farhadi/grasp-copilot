import json

import llm.inference as inf


def test_json_repair_logic_without_model(monkeypatch):
    calls = {"n": 0}

    def fake_load(cfg):
        return object(), object()

    def fake_generate_once(model, tok, messages, cfg):
        calls["n"] += 1
        if calls["n"] == 1:
            return "{\"tool_name\": \"INTERACT\""  # invalid JSON
        return "{\"tool_name\":\"INTERACT\",\"arguments\":{\"type\":\"notify\",\"text\":\"ok\"}}"

    monkeypatch.setattr(inf, "_load_model_and_tokenizer", fake_load)
    monkeypatch.setattr(inf, "_generate_once", fake_generate_once)

    cfg = inf.InferenceConfig(model_name="dummy", adapter_path=None, merged_model_path=None)
    out = inf.generate_json_only("hi", cfg)
    assert out["tool_name"] == "INTERACT"


def test_json_repair_raises_after_second_failure(monkeypatch):
    def fake_load(cfg):
        return object(), object()

    def fake_generate_once(model, tok, messages, cfg):
        return "not json"

    monkeypatch.setattr(inf, "_load_model_and_tokenizer", fake_load)
    monkeypatch.setattr(inf, "_generate_once", fake_generate_once)

    cfg = inf.InferenceConfig(model_name="dummy", adapter_path=None, merged_model_path=None)
    try:
        inf.generate_json_only("hi", cfg)
        assert False, "expected error"
    except ValueError as e:
        assert "RAW" in str(e)

