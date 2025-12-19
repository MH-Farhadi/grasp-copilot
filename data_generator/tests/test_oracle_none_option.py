from data_generator.oracle import OracleState, oracle_decide_tool


def test_oracle_candidate_choice_includes_none_of_them():
    objects = [
        {"id": "o0", "label": "mug", "cell": "A1", "yaw": "N", "is_held": False},
        {"id": "o1", "label": "sugar_box", "cell": "A1", "yaw": "E", "is_held": False},
        {"id": "o2", "label": "tuna_fish_can", "cell": "A2", "yaw": "S", "is_held": False},
    ]
    gripper_hist = [{"cell": "A1", "yaw": "N", "z": "MID"}] * 6
    memory = {"candidates": ["o0", "o1", "o2"], "past_dialogs": [], "n_interactions": 1, "last_tool_calls": [], "excluded_obj_ids": []}
    state = OracleState(intended_obj_id="o0")
    state.awaiting_choice = True
    tool = oracle_decide_tool(objects, gripper_hist, memory, state)
    assert tool["tool"] == "INTERACT"
    assert tool["args"]["kind"] == "QUESTION"
    # Last choice should be None of them, numbered.
    assert "None of them" in tool["args"]["choices"][-1]
    assert tool["args"]["choices"][-1].split(")", 1)[0].isdigit()


