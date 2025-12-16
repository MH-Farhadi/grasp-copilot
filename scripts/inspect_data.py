"""
Quick inspection tool for generated datasets and LLM-prepared data.

Examples:
  # Inspect 3 generator records (episode_id/obs/dialog/tool):
  python scripts/inspect_data.py --file /tmp/grasp_gen.jsonl --mode generator --n 3

  # Inspect 3 contract records (instruction/input/output):
  python scripts/inspect_data.py --file /tmp/grasp_contract.jsonl --mode contract --n 3

  # Inspect 3 chat records (messages):
  python scripts/inspect_data.py --file /tmp/grasp_chat.jsonl --mode chat --n 3
"""

from __future__ import annotations

import argparse
import json
from typing import Dict, List

import _bootstrap  # noqa: F401
from llm import data as data_lib


def _load_lines(path: str, n: int) -> List[str]:
    out: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(line)
            if len(out) >= n:
                break
    return out


def _print_generator(line: str) -> None:
    obj = json.loads(line)
    obs = obj.get("obs", {})
    dialog = obj.get("dialog", [])
    tool = obj.get("target_tool_call", {})
    print(f"- episode_id={obj.get('episode_id')} t={obj.get('t')}")
    print("  tool:", json.dumps(tool, ensure_ascii=False))
    print("  obs keys:", list(obs.keys()))
    print("  dialog len:", len(dialog))


def _print_contract(line: str) -> None:
    obj = json.loads(line)
    print(f"- id={obj.get('id')}")
    print("  instruction:", obj.get("instruction"))
    print("  input keys:", list(json.loads(obj.get("input", "{}")).keys()))
    print("  output:", obj.get("output"))


def _print_chat(line: str) -> None:
    obj = json.loads(line)
    msgs: List[Dict] = obj.get("messages", [])
    print(f"- id={obj.get('id')}")
    for m in msgs:
        role = m.get("role")
        content = m.get("content")
        print(f"  [{role}] {content}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="Path to JSONL file")
    ap.add_argument("--mode", choices=["generator", "contract", "chat"], required=True)
    ap.add_argument("--n", type=int, default=3, help="Number of lines to show")
    args = ap.parse_args()

    lines = _load_lines(args.file, args.n)
    print(f"Showing {len(lines)} examples from {args.file} (mode={args.mode})")

    if args.mode == "generator":
        for ln in lines:
            _print_generator(ln)
    elif args.mode == "contract":
        # Validate upfront for nicer errors.
        data_lib.validate_dataset_contract_jsonl(args.file)
        for ln in lines:
            _print_contract(ln)
    else:
        for ln in lines:
            _print_chat(ln)


if __name__ == "__main__":
    main()


