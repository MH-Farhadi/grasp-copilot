from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from . import grid
from . import yaw as yawlib


@dataclass
class OracleState:
    intended_obj_id: str
    selected_obj_id: Optional[str] = None
    pending_action_obj_id: Optional[str] = None
    awaiting_confirmation: bool = False
    awaiting_help: bool = False
    awaiting_choice: bool = False
    last_prompt_context: Optional[Dict] = None
    # Track recent user rejections to avoid asking the exact same question in a loop.
    last_declined_obj_id: Optional[str] = None
    last_tool_calls: List[str] = field(default_factory=list)


def _tool(tool: str, args: Dict) -> Dict:
    return {"tool": tool, "args": args}


def _interact(kind: str, text: str, choices: List[str], context: Dict, state: OracleState) -> Dict:
    state.last_prompt_context = context
    return _tool("INTERACT", {"kind": kind, "text": text, "choices": choices})


def _top_two_candidates(objects: Sequence[Dict], candidates: Sequence[str], gripper_cell: str) -> Optional[List[Dict]]:
    available = [o for o in objects if o["id"] in set(candidates) and not o["is_held"]]
    if len(available) < 2:
        return None
    scored = [(o, grid.manhattan(gripper_cell, o["cell"])) for o in available]
    scored.sort(key=lambda x: (x[1], x[0]["id"]))
    return [scored[0][0], scored[1][0]]


def _has_yaw_oscillation(gripper_hist: Sequence[Dict]) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Returns (triggered, cell, yaw1, yaw2) to support yaw-struggle prompts.
    """
    if len(gripper_hist) < 6:
        return False, None, None, None
    cells = [g["cell"] for g in gripper_hist]
    yaws = [g["yaw"] for g in gripper_hist]
    cell_counts = Counter(cells)
    dominant_cell, count = cell_counts.most_common(1)[0]
    if count < 4:
        return False, None, None, None

    # Track yaw switches to see if we bounce between two bins.
    unique_order: List[str] = []
    for y in yaws:
        if not unique_order or unique_order[-1] != y:
            unique_order.append(y)
    if len(set(unique_order)) != 2:
        return False, None, None, None
    switches = sum(1 for i in range(1, len(yaws)) if yaws[i] != yaws[i - 1])
    if switches < 3:
        return False, None, None, None
    yaw1, yaw2 = unique_order[0], unique_order[1]
    return True, dominant_cell, yaw1, yaw2


def _has_cell_oscillation(gripper_hist: Sequence[Dict], cell_a: str, cell_b: str) -> bool:
    """
    Detects whether the gripper has been oscillating between two cells recently.
    This supports ambiguity prompts even when last_tool_calls is empty.
    """
    if len(gripper_hist) < 6:
        return False
    cells = [g["cell"] for g in gripper_hist]
    allowed = {cell_a, cell_b}
    # Require both cells to appear at least twice.
    if cells.count(cell_a) < 2 or cells.count(cell_b) < 2:
        return False
    # Require multiple transitions between the two cells.
    transitions = 0
    for i in range(1, len(cells)):
        if cells[i] != cells[i - 1] and {cells[i], cells[i - 1]} <= allowed:
            transitions += 1
    return transitions >= 2


def oracle_decide_tool(objects: Sequence[Dict], gripper_hist: Sequence[Dict], memory: Dict, state: OracleState) -> Dict:
    current_cell = gripper_hist[-1]["cell"]
    candidates = list(memory.get("candidates", []))
    objects_by_id = {o["id"]: o for o in objects}
    current_yaw = gripper_hist[-1]["yaw"]

    # Follow-up action after user confirmed help/approach.
    if state.pending_action_obj_id is not None and state.pending_action_obj_id in objects_by_id:
        target = objects_by_id[state.pending_action_obj_id]
        if current_cell != target["cell"]:
            return _tool("APPROACH", {"obj": target["id"]})
        if current_yaw != target["yaw"]:
            return _tool("ALIGN_YAW", {"obj": target["id"]})
        # Completed the pending action; clear selection to avoid re-confirm loops.
        state.pending_action_obj_id = None
        state.selected_obj_id = None
        state.awaiting_confirmation = False
        state.awaiting_choice = False
        state.awaiting_help = False

    # If we're waiting for a user reply, keep prompting (don't fall through to motion tools).
    if state.awaiting_confirmation:
        obj_id = state.selected_obj_id or state.intended_obj_id
        obj = objects_by_id.get(obj_id)
        if obj:
            question = f"Do you want me to approach the {obj['label']}?"
            choices = ["1) YES", "2) NO"]
            context = {"type": "confirm", "obj_id": obj["id"], "label": obj["label"]}
            return _interact("CONFIRM", question, choices, context, state)
        state.awaiting_confirmation = False

    if state.awaiting_choice:
        top_two = _top_two_candidates(objects, candidates, current_cell)
        if top_two:
            a, b = top_two
            text = (
                f"I notice you are approaching the {a['label']}. "
                f"However, {b['label']} is also close. Which one do you want to grasp?"
            )
            choices = [f"1) {a['label']}", f"2) {b['label']}"]
            context = {"type": "candidate_question", "labels": [a["label"], b["label"]]}
            return _interact("QUESTION", text, choices, context, state)
        state.awaiting_choice = False

    if state.awaiting_help:
        # Re-ask the help prompt if we are still in a yaw-struggle state.
        triggered, dom_cell, yaw1, yaw2 = _has_yaw_oscillation(gripper_hist)
        if triggered:
            target_obj = next((o for o in objects if o["cell"] == dom_cell), None)
            if target_obj and target_obj["yaw"] not in {yaw1, yaw2}:
                text = (
                    f"It looks like you are trying to align to the {target_obj['label']} at {dom_cell}, "
                    f"but the gripper yaw keeps changing ({yaw1} and {yaw2}) instead of matching the object yaw "
                    f"({target_obj['yaw']}). Do you want me to help?"
                )
                choices = ["1) YES", "2) NO"]
                context = {"type": "help", "obj_id": target_obj["id"], "yaws": (yaw1, yaw2, target_obj["yaw"])}
                return _interact("SUGGESTION", text, choices, context, state)
        state.awaiting_help = False

    # Confirmation after a user-picked object.
    if state.selected_obj_id is not None and not state.awaiting_confirmation:
        obj = objects_by_id.get(state.selected_obj_id)
        if obj:
            # Ask to confirm the *next* action we would take (approach vs align yaw),
            # so the post-confirm tool call matches the user's expectation.
            if current_cell != obj["cell"]:
                question = f"Do you want me to approach the {obj['label']}?"
                context = {"type": "confirm", "obj_id": obj["id"], "label": obj["label"], "action": "APPROACH"}
            elif current_yaw != obj["yaw"]:
                question = f"Do you want me to align yaw to the {obj['label']}?"
                context = {"type": "confirm", "obj_id": obj["id"], "label": obj["label"], "action": "ALIGN_YAW"}
            else:
                # Already at the desired pose; no need to confirm another action.
                state.selected_obj_id = None
                state.awaiting_confirmation = False
                state.awaiting_choice = False
                state.awaiting_help = False
                obj = None
            if obj is not None:
                state.awaiting_confirmation = True
                choices = ["1) YES", "2) NO"]
                return _interact("CONFIRM", question, choices, context, state)

    # Candidate clarification when approach evidence is similar.
    #
    # Important: don't ask this every timestep. Gate it so it primarily triggers right after
    # a movement step (APPROACH), which makes it feel like the assistant is reacting to
    # ambiguous motion rather than nagging.
    top_two = _top_two_candidates(objects, candidates, current_cell)
    last_calls = list(memory.get("last_tool_calls", []))
    just_moved = bool(last_calls and last_calls[-1] == "APPROACH")
    if top_two and not state.awaiting_choice and not state.awaiting_confirmation:
        a, b = top_two
        osc = _has_cell_oscillation(gripper_hist, a["cell"], b["cell"])
        allow = just_moved or osc
        if allow:
            dist_a = grid.manhattan(current_cell, a["cell"])
            dist_b = grid.manhattan(current_cell, b["cell"])
            if abs(dist_a - dist_b) <= 1:
                text = (
                    f"I notice you are approaching the {a['label']}. "
                    f"However, {b['label']} is also close. Which one do you want to grasp?"
                )
                choices = [f"1) {a['label']}", f"2) {b['label']}"]
                context = {"type": "candidate_question", "labels": [a["label"], b["label"]]}
                state.awaiting_choice = True
                return _interact("QUESTION", text, choices, context, state)

    # Yaw struggle suggestion.
    triggered, dom_cell, yaw1, yaw2 = _has_yaw_oscillation(gripper_hist)
    if triggered and not state.awaiting_help:
        target_obj = next((o for o in objects if o["cell"] == dom_cell), None)
        if target_obj and target_obj["yaw"] not in {yaw1, yaw2}:
            text = (
                f"It looks like you are trying to align to the {target_obj['label']} at {dom_cell}, "
                f"but the gripper yaw keeps changing ({yaw1} and {yaw2}) instead of matching the object yaw "
                f"({target_obj['yaw']}). Do you want me to help?"
            )
            choices = ["1) YES", "2) NO"]
            context = {"type": "help", "obj_id": target_obj["id"], "yaws": (yaw1, yaw2, target_obj["yaw"])}
            state.awaiting_help = True
            return _interact("SUGGESTION", text, choices, context, state)

    # Default policy: move toward the intended object or align yaw when co-located.
    intended = objects_by_id[state.intended_obj_id]
    if current_cell != intended["cell"]:
        return _tool("APPROACH", {"obj": intended["id"]})
    if current_yaw != intended["yaw"]:
        return _tool("ALIGN_YAW", {"obj": intended["id"]})

    # If already aligned and close, gently re-confirm intent.
    if not state.awaiting_confirmation:
        state.awaiting_confirmation = True
        text = f"Do you want me to approach the {intended['label']}?"
        choices = ["1) YES", "2) NO"]
        context = {"type": "confirm", "obj_id": intended["id"], "label": intended["label"]}
        return _interact("CONFIRM", text, choices, context, state)

    # Waiting for a YES/NO; keep prompting.
    text = f"Do you want me to approach the {intended['label']}?"
    choices = ["1) YES", "2) NO"]
    context = {"type": "confirm", "obj_id": intended["id"], "label": intended["label"]}
    return _interact("CONFIRM", text, choices, context, state)


def validate_tool_call(tool_call: Dict) -> None:
    if not isinstance(tool_call, dict) or set(tool_call.keys()) != {"tool", "args"}:
        raise ValueError("Tool call must be {tool, args}")
    tool = tool_call["tool"]
    args = tool_call["args"]
    if tool not in {"INTERACT", "APPROACH", "ALIGN_YAW"}:
        raise ValueError(f"Invalid tool: {tool}")
    if not isinstance(args, dict):
        raise ValueError("args must be an object")
    if tool == "INTERACT":
        required_keys = {"kind", "text", "choices"}
        if set(args.keys()) != required_keys:
            raise ValueError("INTERACT args must be {kind,text,choices}")
        if args["kind"] not in {"QUESTION", "SUGGESTION", "CONFIRM"}:
            raise ValueError("Invalid INTERACT.kind")
        if not isinstance(args["text"], str):
            raise ValueError("INTERACT.text must be a string")
        choices = args["choices"]
        if not isinstance(choices, list) or not choices or not all(isinstance(c, str) for c in choices):
            raise ValueError("INTERACT.choices must be a non-empty list of strings")
        for c in choices:
            prefix = c.split(")", 1)[0]
            if not prefix.isdigit():
                raise ValueError("INTERACT.choices must start with numbered prefixes like '1)'")
    elif tool in {"APPROACH", "ALIGN_YAW"}:
        if set(args.keys()) != {"obj"} or not isinstance(args["obj"], str):
            raise ValueError(f"{tool} args must be {{obj}}")
