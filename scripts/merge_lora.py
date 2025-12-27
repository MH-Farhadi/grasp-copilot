import argparse

import _bootstrap  # noqa: F401
from llm.train import merge_lora


def main() -> None:
    ap = argparse.ArgumentParser(description="DEPRECATED: merge a LoRA adapter into a standalone model. New training runs write merged models directly.")
    ap.add_argument("--base_model_name", type=str, required=True)
    ap.add_argument("--adapter_dir", type=str, required=True)
    ap.add_argument("--output_dir", type=str, required=True)
    args = ap.parse_args()
    merge_lora(args.base_model_name, args.adapter_dir, args.output_dir)


if __name__ == "__main__":
    main()

