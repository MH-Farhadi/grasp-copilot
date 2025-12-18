from __future__ import annotations

import argparse
import json
import os
import random
from typing import Dict, List, Optional, Tuple

from .episode import Episode, OBJECT_LABELS, write_jsonl
from .oracle import OracleState, oracle_decide_tool, validate_tool_call


def _deepcopy_memory(mem: Dict) -> Dict:
    return {
        "n_interactions": int(mem["n_interactions"]),
        "past_dialogs": list(mem["past_dialogs"]),
        "candidates": list(mem["candidates"]),
        "last_tool_calls": list(mem["last_tool_calls"]),
    }


def _strip_choice_label(choice: str) -> str:
    parts = choice.split(")", 1)
    return parts[1].strip() if len(parts) == 2 else choice.strip()


def _simulate_user_response(
    rng: random.Random,
    tool_call: Dict,
    episode: Episode,
    memory: Dict,
    state: OracleState,
) -> None:
    """
    Apply the user-simulation rules to update memory and oracle state.
    """
    if tool_call["tool"] != "INTERACT":
        state.last_prompt_context = None
        return

    ctx = state.last_prompt_context or {}
    # If the oracle is explicitly waiting for a reply, always respond.
    # Otherwise, allow the simulated user to be occasionally quiet.
    must_respond = bool(state.awaiting_choice or state.awaiting_confirmation or state.awaiting_help)
    if (not must_respond) and rng.random() >= 0.6:
        return

    def append_user(content: str) -> None:
        memory["past_dialogs"].append({"role": "user", "content": content})

    if ctx.get("type") == "candidate_question":
        labels = ctx.get("labels", [])
        intended_label = episode.intended_obj().label
        declined_label: Optional[str] = None
        if state.last_declined_obj_id is not None:
            for o in episode.objects:
                if o.id == state.last_declined_obj_id:
                    declined_label = o.label
                    break
        if labels and intended_label in labels and rng.random() < 0.7:
            # If the user just declined this object, they are less likely to pick it again immediately.
            if declined_label is not None and intended_label == declined_label and len(labels) >= 2 and rng.random() < 0.85:
                others = [l for l in labels if l != declined_label]
                pick = rng.choice(others) if others else intended_label
            else:
                pick = intended_label
        else:
            pick = rng.choice(labels) if labels else _strip_choice_label(rng.choice(tool_call["args"]["choices"]))
        append_user(pick)
        for o in episode.objects:
            if o.label == pick:
                state.selected_obj_id = o.id
                # Treat the user's selection as the new "intended" goal to avoid
                # oscillating back to the original hidden intent.
                state.intended_obj_id = o.id
                break
        state.awaiting_choice = False
        state.awaiting_confirmation = False
    elif ctx.get("type") in {"confirm", "help"}:
        obj_id = ctx.get("obj_id")
        aligns = obj_id == episode.intended_obj_id
        yes_prob = 0.75 if aligns else 0.25
        resp = "YES" if rng.random() < yes_prob else "NO"
        append_user(resp)
        if resp == "YES" and obj_id:
            state.pending_action_obj_id = obj_id
            state.selected_obj_id = obj_id
            # If the user confirmed, lock the goal to that object.
            state.intended_obj_id = obj_id
            state.last_declined_obj_id = None
        elif resp == "NO" and obj_id:
            state.last_declined_obj_id = obj_id
        # Once the user answered, don't keep re-confirming the same selection.
        # The oracle can rely on pending_action_obj_id (on YES) to proceed.
        if ctx["type"] in {"confirm", "help"}:
            state.selected_obj_id = None
        if ctx["type"] == "confirm":
            state.awaiting_confirmation = False
        if ctx["type"] == "help":
            state.awaiting_help = False
    else:
        # Fallback: respect yes/no prompts with semantic logging.
        labels = [c for c in tool_call["args"].get("choices", [])]
        yes_prob = 0.5
        resp = "YES" if rng.random() < yes_prob else "NO"
        if any("YES" in l.upper() for l in labels):
            append_user(resp)

    state.last_prompt_context = None


def _schema_validate_record(rec: Dict) -> None:
    for k in ("episode_id", "t", "objects", "gripper_hist", "memory", "target_tool_call"):
        if k not in rec:
            raise ValueError(f"Missing key: {k}")
    if len(rec["gripper_hist"]) != 6:
        raise ValueError("gripper_hist must have length 6")
    validate_tool_call(rec["target_tool_call"])


def generate(episodes: int, seed: int) -> Tuple[List[Dict], Dict]:
    rng = random.Random(seed)
    records: List[Dict] = []
    tool_counts: Dict[str, int] = {"INTERACT": 0, "APPROACH": 0, "ALIGN_YAW": 0}

    for episode_id in range(episodes):
        n_obj = rng.randint(2, min(10, len(OBJECT_LABELS)))
        ep = Episode(rng=rng, episode_id=episode_id, n_obj=n_obj)
        state = OracleState(intended_obj_id=ep.intended_obj_id)
        memory: Dict = {
            "n_interactions": 0,
            "past_dialogs": [],
            "candidates": ep.gripper_candidates(max_dist=1),
            "last_tool_calls": [],
        }

        for t in range(ep.T):
            # Snapshot before choosing the tool call.
            memory["candidates"] = ep.gripper_candidates(max_dist=1)
            record = {
                "episode_id": episode_id,
                "t": t,
                "objects": [o.to_record() for o in ep.objects],
                "gripper_hist": [p.to_record() for p in ep.gripper_hist],
                "memory": _deepcopy_memory(memory),
            }

            tool_call = oracle_decide_tool(record["objects"], record["gripper_hist"], memory, state)
            validate_tool_call(tool_call)
            record["target_tool_call"] = tool_call
            _schema_validate_record(record)
            records.append(record)

            tool_counts[tool_call["tool"]] += 1

            # Update dialog and interaction counters.
            if tool_call["tool"] == "INTERACT":
                memory["n_interactions"] += 1
                memory["past_dialogs"].append({"role": "assistant", "content": tool_call["args"]["text"]})

            _simulate_user_response(rng, tool_call, ep, memory, state)

            # Maintain a short history of tool calls for memory logging.
            memory["last_tool_calls"].append(tool_call["tool"])
            memory["last_tool_calls"] = memory["last_tool_calls"][-3:]

            # Apply tool effects then simulate teleop toward intent.
            ep.apply_tool(tool_call)
            if t < ep.T - 1:
                # If the assistant executed a non-interactive tool, the human is less likely
                # to keep fighting the motion on the very next step. This reduces unrealistic
                # "ALIGN_YAW spam" / oscillatory behavior.
                skip_user_motion = tool_call["tool"] != "INTERACT" and rng.random() < 0.85
                if not skip_user_motion:
                    ep.apply_user_motion()

            # If we've reached the currently intended object pose (cell + yaw),
            # stop the episode early. This makes APPROACH/ALIGN_YAW naturally "final"
            # actions and avoids long post-goal chat loops.
            intended = ep.get_obj(state.intended_obj_id)
            g = ep.gripper_hist[-1]
            if g.cell == intended.cell and g.yaw == intended.yaw:
                break

        # Reset per-episode flags that should not leak; none currently.
        state.last_tool_calls.clear()

    stats = {"tool_distribution": tool_counts}
    return records, stats


def main(argv: Optional[List[str]] = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, required=True)
    ap.add_argument("--out", type=str, required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    records, stats = generate(episodes=args.episodes, seed=args.seed)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    write_jsonl(args.out, records)
    with open(args.out + ".stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()

