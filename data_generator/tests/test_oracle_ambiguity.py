from data_generator.oracle import OracleState, oracle_decide_tool


def test_oracle_ambiguity_triggers_interact_question():
    objects = [
        {"id": "o0", "label": "mug", "cell": "A1", "yaw": "N", "is_held": False},
        {"id": "o1", "label": "sugar_box", "cell": "A2", "yaw": "E", "is_held": False},
        {"id": "o2", "label": "tuna_fish_can", "cell": "C3", "yaw": "S", "is_held": False},
    ]
    gripper_hist = [
        {"cell": "A1", "yaw": "N", "z": "HIGH"},
        {"cell": "A1", "yaw": "N", "z": "HIGH"},
        {"cell": "A2", "yaw": "N", "z": "HIGH"},
        {"cell": "A2", "yaw": "N", "z": "HIGH"},
        {"cell": "A1", "yaw": "N", "z": "HIGH"},
        {"cell": "A2", "yaw": "N", "z": "HIGH"},
    ]
    memory = {"candidates": ["o0", "o1"], "past_dialogs": [], "n_interactions": 0, "last_tool_calls": []}
    state = OracleState(intended_obj_id="o0")
    tool = oracle_decide_tool(objects, gripper_hist, memory, state)
    assert tool["tool"] == "INTERACT"
    assert tool["args"]["kind"] == "QUESTION"
    labels = {c.split(")", 1)[1].strip() for c in tool["args"]["choices"]}
    assert labels == {"mug", "sugar_box"}
    assert all(c.startswith(("1)", "2)")) for c in tool["args"]["choices"])
