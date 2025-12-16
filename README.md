# grasp-copilot
a copilot llm for suggesting grasp assistives.

## LLM fine-tuning + inference

All commands must activate the `talm` environment first:

```bash
conda activate talm
```

### Prepare LLM data (adapter over existing generator JSONL)

```bash
conda activate talm
python scripts/prepare_llm_data.py --generator_jsonl data.jsonl --out_contract llm_contract.jsonl --out_chat llm_chat.jsonl
```

### Train SFT + LoRA / QLoRA

```bash
conda activate talm
python scripts/train_sft_lora.py --train_path llm_contract.jsonl --valid_path llm_contract.jsonl --output_dir outputs/qwen_lora --model_name Qwen/Qwen2.5-7B-Instruct --use_4bit
```

### Merge LoRA (optional)

```bash
conda activate talm
python scripts/merge_lora.py --base_model_name Qwen/Qwen2.5-7B-Instruct --adapter_dir outputs/qwen_lora --output_dir outputs/qwen_merged
```

### Inference demo (JSON-only)

```bash
conda activate talm
python scripts/inference_demo.py --model_name Qwen/Qwen2.5-7B-Instruct --adapter_path outputs/qwen_lora --prompt 'Return {"tool_name":"INTERACT","arguments":{"type":"notify","text":"ok"}}'
```
