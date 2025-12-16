import json
from pathlib import Path

from llm.data import (
    convert_contract_to_qwen_chat_jsonl,
    convert_generator_jsonl_to_contract,
    validate_dataset_contract_jsonl,
)


def test_validate_and_convert_contract_to_chat(tmp_path: Path):
    contract = tmp_path / "contract.jsonl"
    contract.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "0",
                        "instruction": "Return a tool call.",
                        "input": "{\"obs\":{}}",
                        "output": "{\"tool_name\":\"INTERACT\",\"arguments\":{\"type\":\"notify\",\"text\":\"ok\"}}",
                    }
                )
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    validate_dataset_contract_jsonl(str(contract))

    chat = tmp_path / "chat.jsonl"
    convert_contract_to_qwen_chat_jsonl(str(contract), str(chat))
    line = chat.read_text(encoding="utf-8").strip()
    obj = json.loads(line)
    assert obj["messages"][0]["role"] == "system"
    assert obj["messages"][1]["role"] == "user"
    assert obj["messages"][2]["role"] == "assistant"


def test_convert_generator_jsonl_to_contract(tmp_path: Path):
    gen = tmp_path / "gen.jsonl"
    gen.write_text(
        json.dumps(
            {
                "episode_id": 1,
                "t": 2,
                "obs": {"objects": [], "gripper_hist": [], "candidates": [], "last_action_outcome": "none"},
                "dialog": [{"role": "user", "content": "mug"}],
                "target_tool_call": {"tool_name": "SELECT_TARGET", "arguments": {"obj_id": "o0"}},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "contract.jsonl"
    convert_generator_jsonl_to_contract(str(gen), str(out))
    validate_dataset_contract_jsonl(str(out))

