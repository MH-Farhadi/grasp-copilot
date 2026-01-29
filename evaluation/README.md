# Evaluation Pipeline for PRIME Paper

This directory contains the offline executive benchmark for evaluating LLM-based grasp assistance.

## Quick Start

### Run Full Benchmark (Fine-tuned + Heuristics)

```bash
cd grasp-copilot
python -m evaluation.run_full_benchmark
```

### Run with Specific Options

```bash
# Quick test with fewer examples
python -m evaluation.run_full_benchmark --max_examples 100

# Include zero-shot baselines (slower, needs HF access)
python -m evaluation.run_full_benchmark --include_zero_shot

# Custom contract JSONL
python -m evaluation.run_full_benchmark \
    --contract_jsonl data/runs/010/llm_contract.jsonl \
    --out_dir evaluation/eval_outputs/my_benchmark
```

### Run Individual Model Evaluation

```bash
python -m evaluation.offline_exec_benchmark \
    --contract_jsonl data/runs/010/llm_contract.jsonl \
    --models "Qwen7B-FT=models/qwen2_5_7b_instruct_ft" \
    --include_heuristic \
    --include_heuristic_always_ask \
    --out_dir evaluation/eval_outputs/benchmark_run \
    --dump_mistakes
```

## Models Evaluated

### Fine-tuned Models
- **Qwen2.5-7B-FT**: `models/qwen2_5_7b_instruct_ft`
- **Qwen2.5-3B-FT**: `models/qwen2_5_3b_instruct_ft`

### Zero-shot Models (optional, with `--include_zero_shot`)
- **Qwen2.5-7B-ZS**: `Qwen/Qwen2.5-7B-Instruct`
- **Qwen2.5-3B-ZS**: `Qwen/Qwen2.5-3B-Instruct`

### Heuristic Baselines
- **H1_ask_if_ambiguous**: Asks only when multiple candidates exist
- **H2_always_ask**: Always confirms before any motion

## Metrics

### Primary Metrics (Paper Table 1)
| Metric | Description |
|--------|-------------|
| `tool_accuracy` | Correct tool type (INTERACT/APPROACH/ALIGN_YAW) |
| `motion_obj_accuracy` | Correct target object when motion tool |
| `interact_kind_accuracy` | Correct dialog type (QUESTION/CONFIRM/SUGGESTION) |
| `schema_valid_rate` | Valid JSON + schema compliance |
| `strict_exact_rate` | Exact match (ignoring INTERACT text) |

### Secondary Metrics
| Metric | Description |
|--------|-------------|
| `motion_tool_accuracy` | APPROACH vs ALIGN_YAW correctness |
| `interact_choices_valid_rate` | Choices list ≤ 5 items |
| `json_valid_rate` | Parseable JSON output |

### Breakdowns
- **Per-context**: Accuracy by dialog context type (confirm, candidate_choice, etc.)
- **Per-mode**: Accuracy by user mode (translation, rotation, gripper)
- **Per-candidates**: Accuracy by number of nearby candidates

## Output Files

| File | Description |
|------|-------------|
| `summary_all.json` | Full results with all metrics |
| `summary_all.csv` | Tabular summary for import |
| `context_breakdown.csv` | Per-context accuracy table |
| `confusion_matrices.csv` | Tool confusion matrices |
| `mistakes_*.jsonl` | Error examples for analysis |

## Example Results Table

```
====================================================================================================
BENCHMARK RESULTS SUMMARY
====================================================================================================
Model                     Tool Acc   Mot.Obj   Int.Kind     Schema     Strict        N
----------------------------------------------------------------------------------------------------
Qwen2.5-7B-FT               0.9523     0.8912     0.9801     0.9989     0.8234     5658
Qwen2.5-3B-FT               0.9312     0.8567     0.9654     0.9978     0.7891     5658
H1_ask_if_ambiguous         0.7823     0.6234     0.8901     1.0000     0.5123     5658
H2_always_ask               0.5012     0.0000     0.9234     1.0000     0.2345     5658
====================================================================================================
```
