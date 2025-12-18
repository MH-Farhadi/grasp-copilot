from data_generator.oracle import OracleState, oracle_decide_tool


def test_oracle_struggle_triggers_suggestion_on_oscillation():
    objects = [{"id": "o0", "label": "mug", "cell": "B2", "yaw": "S", "is_held": False}]
    gripper_hist = [
        {"cell": "B2", "yaw": "N", "z": "MID"},
        {"cell": "B2", "yaw": "E", "z": "MID"},
        {"cell": "B2", "yaw": "N", "z": "MID"},
        {"cell": "B2", "yaw": "E", "z": "MID"},
        {"cell": "B2", "yaw": "N", "z": "MID"},
        {"cell": "B2", "yaw": "E", "z": "MID"},
    ]
    memory = {"candidates": ["o0"], "past_dialogs": [], "n_interactions": 0, "last_tool_calls": []}
    state = OracleState(intended_obj_id="o0")
    tool = oracle_decide_tool(objects, gripper_hist, memory, state)
    assert tool["tool"] == "INTERACT"
    # New flow gates on intent first, then offers help.
    assert tool["args"]["kind"] == "QUESTION"
    assert "struggling aligning" in tool["args"]["text"]
