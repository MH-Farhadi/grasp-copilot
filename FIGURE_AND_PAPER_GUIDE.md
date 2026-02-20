# PRIME Paper — Figure Design Guide & Paper Suggestions

This document describes the benchmark data available in
`evaluation/eval_outputs/paper_benchmark_run001/`, proposes specific figures for
the IROS 2026 submission, and gives broader paper-editing suggestions.

---

## 1. Available Benchmark Data at a Glance

Six "executives" were evaluated on the same 1 947-example contract JSONL
(102 motion examples, 1 845 INTERACT examples):

| Short name | Kind | Parameters | Training |
|---|---|---|---|
| **Qwen2.5-7B-FT** | LLM | 7 B | Full SFT on oracle data |
| **Qwen2.5-3B-FT** | LLM | 3 B | Full SFT on oracle data |
| **Qwen2.5-7B-ZS** | LLM | 7 B | Zero-shot (no task-specific training) |
| **Qwen2.5-3B-ZS** | LLM | 3 B | Zero-shot (no task-specific training) |
| **H1 (ask-if-ambiguous)** | Heuristic | — | Rule-based |
| **H2 (always-ask)** | Heuristic | — | Rule-based (never issues motion) |

Key metrics already computed (in `summary_all.csv`):

| Metric | 7B-FT | 3B-FT | 7B-ZS | 3B-ZS | H1 | H2 |
|---|---|---|---|---|---|---|
| Tool accuracy | 99.4% | 98.7% | 36.1% | 16.6% | 92.9% | 94.8% |
| Motion-obj accuracy | 94.1% | 93.1% | 23.5% | 15.4% | 16.7% | 0.0% |
| Motion-tool accuracy | 90.2% | 81.4% | 55.9% | 71.8% | 21.6% | 0.0% |
| Interact-kind accuracy | 99.6% | 99.3% | 34.2% | 2.8% | 83.7% | 85.1% |
| Schema-valid rate | 100% | 99.6% | 68.1% | 89.6% | 100% | 100% |
| JSON-valid rate | 100% | 100% | 100% | 95.0% | 100% | 100% |
| Strict exact match | 97.2% | 93.4% | 0.5% | 2.6% | 7.1% | 7.7% |

Additional breakdowns available:
- **Per dialog-context** accuracy (7 context types, in `context_breakdown.csv`)
- **Confusion matrices** per model (in `confusion_matrices.csv`)
- **Per user-mode** accuracy (translation / rotation / gripper)
- **Per candidate-count** accuracy (0–6+ candidates)

---

## 2. Proposed Figures

### Figure A — "Main Comparison" Grouped Bar Chart  *(highest priority)*

**What it shows.** A single grouped bar chart comparing all six executives
across 3–4 key metrics side by side.

**Recommended metrics (bars per group):**
1. **Tool Accuracy** — did the model pick the right tool type (INTERACT vs APPROACH vs ALIGN_YAW)?
2. **Motion-Object Accuracy** — when a motion tool was needed, did it target the correct object?
3. **INTERACT-Kind Accuracy** — when an INTERACT was needed, did it choose the correct sub-type (QUESTION / SUGGESTION / CONFIRM)?
4. **Strict Exact Match** — full JSON output matches the oracle exactly.

**Layout:**
- X-axis: 6 groups, one per executive.
  Order: `Qwen 7B (FT)`, `Qwen 3B (FT)`, `Qwen 7B (ZS)`, `Qwen 3B (ZS)`, `H1: ask-if-ambig`, `H2: always-ask`.
  Visually separate LLMs from heuristics with a small gap or vertical dashed line.
- Y-axis: Accuracy (0–100 %).
- 4 bars per group, distinguishable colors (e.g. blue, orange, green, gray).
- Annotate exact values on top of each bar (or a subset for the most important ones).
- Add a thin horizontal dashed line at the oracle ceiling (100 %) for reference.

**Design notes:**
- Use IEEE single-column width (~3.5 in) if space is tight, or double-column
  (~7 in) for readability. A double-column figure is recommended because 6×4 bars
  are hard to read at single-column width.
- Use `matplotlib` with the `seaborn` "muted" or "colorblind" palette for
  accessibility.
- Keep the figure self-contained: a reader should understand the main result
  (fine-tuned LLMs dramatically outperform zero-shot and heuristics) at a glance.

**Story the figure tells:**
- Fine-tuned models (especially 7B) are near-perfect on tool selection and
  INTERACT-kind, while zero-shot models collapse.
- Heuristics achieve high *tool accuracy* (~93–95 %) but fail on motion-object
  accuracy (0–17 %) and strict exact match (~7 %).
- This proves the LLM's value: it learns the *full policy* (when + what to ask,
  which object to act on), not just the coarse tool choice.

**Rough ASCII layout:**

```
  100% ┬──────────────────────────────────────────────────
       │ ████  ████                    ████  ████
       │ ████  ████                    ████  ████
       │ ████  ████                    ████  ████
   75% │ ████  ████                    ████  ████
       │ ████  ████      ▓▓▓▓                ████
   50% │ ████  ████      ▓▓▓▓                ████
       │ ████  ████      ▓▓▓▓  ▒▒▒▒
   25% │ ████  ████      ▓▓▓▓  ▒▒▒▒
       │                       ▒▒▒▒
    0% ┴──────────────────────────────────────────────────
        7B-FT  3B-FT   7B-ZS  3B-ZS   H1     H2
       ├── LLM (fine-tuned) ──┤├─ LLM (zero-shot)─┤├ heuristic ┤

        █ Tool acc   ▓ Motion-obj acc   ░ INTERACT-kind acc   ▒ Strict exact
```

---

### Figure B — Per-Context Accuracy Heatmap  *(high priority)*

**What it shows.** A 6-row × 7-column heatmap showing tool accuracy per
dialog-context type for each executive.

**Rows:** 6 executives (same order as Figure A).

**Columns (context types):**
1. `no_context` (n=1003) — first turn, no prior dialog
2. `intent_gate_candidates` (n=446) — system is probing intent among candidates
3. `candidate_choice` (n=177) — user choosing from an object menu
4. `confirm` (n=179) — user confirming before action execution
5. `mode_select` (n=49) — choosing between APPROACH / ALIGN_YAW
6. `intent_gate_yaw` (n=7) — yaw-specific intent gate
7. `anything_else` (n=86) — catch-all "anything else?" follow-ups

**Design notes:**
- Color-code cells from red (0 %) through white (50 %) to dark blue/green (100 %).
- Print the numerical value inside each cell.
- This is a natural IEEE double-column figure.
- Below the heatmap, add a single row showing `n` per column so the reader
  knows sample sizes.

**Story:** Fine-tuned models are uniformly dark (high accuracy) across all
contexts. Zero-shot models show patchy failures, especially on structured contexts
like `confirm` and `candidate_choice`. Heuristics are strong on INTERACT-heavy
contexts but collapse on `confirm` (because they never issue motion).

---

### Figure C — Confusion Matrices (Side-by-Side)  *(medium priority)*

**What it shows.** Two 3×3 row-normalized confusion matrices comparing the best
fine-tuned model (7B-FT) with the best zero-shot model (7B-ZS).

**Axes:** Ground-truth tool (rows) vs. predicted tool (columns):
APPROACH, ALIGN_YAW, INTERACT.

**Raw data (from `confusion_matrices.csv`):**

*Qwen 7B-FT:*
|  | APPROACH | ALIGN_YAW | INTERACT |
|---|---|---|---|
| APPROACH | **51** | 4 | 0 |
| ALIGN_YAW | 5 | **41** | 1 |
| INTERACT | 0 | 1 | **1844** |

*Qwen 7B-ZS:*
|  | APPROACH | ALIGN_YAW | INTERACT |
|---|---|---|---|
| APPROACH | **32** | 16 | 7 |
| ALIGN_YAW | 21 | **25** | 1 |
| INTERACT | 713 | 487 | **645** |

**Design notes:**
- Place two square heatmaps side by side, each with row-normalized values
  (probabilities).
- Annotate each cell with the probability (2 decimal places).
- Diagonal should be dark; off-diagonal should be light.
- Title: "(a) Qwen 7B (FT)" and "(b) Qwen 7B (ZS)".

**Story:** 7B-FT has a near-perfect diagonal. 7B-ZS massively over-predicts
APPROACH and ALIGN_YAW when the oracle intended INTERACT — it
"hallucinates" physical actions when it should be asking the user.

---

### Figure D — Output Reliability Stacked Bars  *(medium priority)*

**What it shows.** For each executive, a stacked bar decomposing outputs into:
valid JSON + valid schema (green), valid JSON + invalid schema (yellow),
invalid JSON (red).

| Model | Valid JSON+Schema | Valid JSON, Bad Schema | Invalid JSON |
|---|---|---|---|
| 7B-FT | 100.0% | 0.0% | 0.0% |
| 3B-FT | 99.6% | 0.4% | 0.0% |
| 7B-ZS | 68.1% | 31.9% | 0.0% |
| 3B-ZS | 89.6% | 5.4% | 5.0% |
| H1 | 100.0% | 0.0% | 0.0% |
| H2 | 100.0% | 0.0% | 0.0% |

**Story:** Fine-tuning completely solves the output-format problem. Zero-shot
7B produces valid JSON but frequently violates the tool-call schema (32 %);
3B-ZS additionally produces ~5 % unparseable JSON. Heuristics are 100 % valid
by construction.

---

### Figure E — Accuracy vs. Inference Throughput Scatter  *(low priority, optional)*

**What it shows.** Scatter plot with X = examples/second, Y = tool accuracy.
Each point is one executive.

This figure is hardware-dependent and may be less appropriate for a venue
submission unless you want to emphasize deployability. Consider including it
only if you have consistent hardware (e.g. single A100 or H100) for all runs.

---

### Figure F — Per-Candidate-Count Line Chart  *(optional, supplement)*

**What it shows.** X-axis = number of candidate objects (0, 1, 2, 3, 4, 5, 6+).
Y-axis = tool accuracy. One line per executive.

**Story:** Heuristics and zero-shot models degrade as candidate count grows;
fine-tuned models remain flat.

---

## 3. How to Produce the Figures

The repo already has a plotting script at
`evaluation/plots/make_offline_exec_figures.py` that generates versions of
Figures A, B, D, and E plus confusion matrices. To run:

```bash
conda activate llm
python -m evaluation.plots.make_offline_exec_figures \
  --run_dir evaluation/eval_outputs/paper_benchmark_run001 \
  --out_dir evaluation/plots
```

For the paper, you will likely want to customize colors, fonts (Times New Roman
or Computer Modern for IEEE), and sizes. Key tips:

- Use `matplotlib.rcParams["font.family"] = "serif"` for IEEE style.
- Target 300 DPI minimum; save as PDF for vector graphics.
- Figure width: 3.5 in (single-column) or 7.0 in (double-column) for IEEEtran.

---

## 4. Reference Papers with Similar Figures

These papers have comparison figures (grouped bar charts, heatmaps, confusion
matrices) that are close analogues to what PRIME needs. Check them for visual
inspiration:

1. **ToolLLM / ToolBench** (Qin et al., NeurIPS 2024)
   - Grouped bar chart comparing LLaMA-based ToolLLaMA vs. ChatGPT vs. baselines
     across API tool-use tasks. Shows pass rate by category.
   - *Relevant for:* Figure A style — multi-bar comparison of LLM sizes and baselines.

2. **Berkeley Function Calling Leaderboard (BFCL)** (Gorilla project, ICML 2025)
   - Detailed per-category accuracy tables and "wagon wheel" (radar) charts
     comparing dozens of models on function-calling correctness.
   - *Relevant for:* Figure B style — per-context breakdown heatmap / radar chart.

3. **SayCan** (Ahn et al., 2022, "Do As I Can, Not As I Say")
   - Bar chart showing plan success rate for SayCan vs. LLM-only vs. affordance-only
     across task categories.
   - *Relevant for:* the LLM vs. heuristic comparison; shows how grounding improves
     over pure LLM reasoning.

4. **Inner Monologue** (Huang et al., 2022)
   - Success-rate comparison (grouped bars) across feedback types: no feedback,
     scene description, success detection, human feedback.
   - *Relevant for:* ablation-style grouped bars like your ZS vs FT vs heuristic.

5. **DELTA: Decomposed Efficient Long-Term Robot Task Planning** (ICRA 2025)
   - Grouped bar chart: LLM-only vs. DELTA (LLM + decomposition + PDDL) vs.
     classical baselines. Shows success rate and planning time.
   - *Relevant for:* the "LLM + structure vs. pure heuristic" argument.

6. **OpenVLA-OFT** (Kim et al., 2025, "Fine-Tuning Vision-Language-Action Models")
   - Bar chart ablation over fine-tuning strategies on LIBERO benchmark
     (76.5 % -> 97.1 %). Confusion-matrix-like per-task heatmaps.
   - *Relevant for:* the fine-tuning ablation narrative; similar "dramatic
     improvement from fine-tuning" story.

7. **MMRo** (arXiv 2406.19693, 2024)
   - Radar chart showing per-capability scores (perception, planning, reasoning,
     safety) for multimodal LLMs acting as robot "brains."
   - *Relevant for:* an alternative Figure B layout using a radar/spider chart
     instead of a heatmap.

8. **Butter-Bench** (arXiv 2510.21860, 2025)
   - Bar chart comparing standard vs. fine-tuned LLMs on embodied reasoning.
     Shows that fine-tuning for embodied tasks does not always help.
   - *Relevant for:* contrast with your result where fine-tuning *does* help
     dramatically — a useful point of discussion.

---

## 5. Recommended Main Table (for the paper body)

In addition to figures, include a summary table in the paper body. This is
standard for IROS / ICRA. Format suggestion:

**Table I: Offline Executive Benchmark Results**

| Executive | Tool Acc. | Motion-Obj Acc. | INTERACT-Kind Acc. | Schema Valid | Exact Match |
|---|---|---|---|---|---|
| Qwen 7B (FT) | **99.4** | **94.1** | **99.6** | 100.0 | **97.2** |
| Qwen 3B (FT) | 98.7 | 93.1 | 99.3 | 99.6 | 93.4 |
| Qwen 7B (ZS) | 36.1 | 23.5 | 34.2 | 68.1 | 0.5 |
| Qwen 3B (ZS) | 16.6 | 15.4 | 2.8 | 89.6 | 2.6 |
| H1: ask-if-ambig | 92.9 | 16.7 | 83.7 | 100.0 | 7.1 |
| H2: always-ask | 94.8 | 0.0 | 85.1 | 100.0 | 7.7 |

Bold the best value in each column. Add a footnote with n=1947 examples,
102 motion, 1845 INTERACT.

---

## 6. Suggestions for Additional Paper Content

### 6.1. Fill in Section IV (Experiments)

The current `root.tex` has empty `\subsection{Simulation}` and
`\subsection{Experimental design}` stubs. Suggested structure:

```
IV. EXPERIMENTS
  A. Dataset Generation
     - Describe the oracle policy and episode simulation.
     - Number of episodes, objects (YCB subset), grid size, control modes.
     - Dataset statistics: 10K episodes, rebalanced split, train/test.

  B. Training Setup
     - Models: Qwen2.5-3B-Instruct, Qwen2.5-7B-Instruct.
     - Training: full SFT on contract JSONL, LoRA config (r=8, alpha=16),
       learning rate, batch size, epochs.
     - Hardware: GPU type, training time.

  C. Baselines
     - H1 (ask-if-ambiguous): always emits INTERACT unless only one candidate
       remains; never issues motion tools.
     - H2 (always-ask): always emits INTERACT, never issues motion.
     - Zero-shot: same Qwen models with the task system prompt but no fine-tuning.

  D. Evaluation Protocol
     - Offline next-tool-call prediction on held-out contract JSONL.
     - Metrics: tool accuracy, motion-object accuracy, INTERACT-kind accuracy,
       schema validity, strict exact match.
     - Describe validation through oracle's validate_tool_call().
```

### 6.2. Add a Results Section (Section V)

```
V. RESULTS
  A. Overall Performance (reference Table I and Figure A)
  B. Per-Context Analysis (reference Figure B heatmap)
  C. Confusion Analysis (reference Figure C)
  D. Output Reliability (reference Figure D or a short paragraph)
```

### 6.3. Additional Figures to Consider

- **Training curve** (loss vs. steps for 3B-FT and 7B-FT): Shows convergence
  speed, useful if you have the training logs.

- **Qualitative example** (already have Fig. 3 in the paper): Consider adding
  a second example showing a *failure mode* of zero-shot or heuristic, to make
  the quantitative gains concrete.

- **Ablation: rebalanced vs. original dataset**: If you have eval results for
  models trained with and without rebalancing, a small grouped bar chart
  would strengthen the data-engineering contribution.

- **User-mode breakdown** (translation vs. rotation vs. gripper): A small table
  or figure showing that fine-tuned models are robust across modes, while ZS
  models particularly struggle in rotation mode.

### 6.4. Paper Structure Tweaks

- The **abstract** is currently one sentence. Expand to ~150 words covering
  problem, method (LLM executive + symbolic state + minimal interaction),
  key result (e.g. "99.4 % tool accuracy with a 7B fine-tuned model vs. 36 %
  zero-shot"), and implication.

- **Contributions list** (end of Section I): Add a fourth bullet about the
  benchmark and evaluation methodology — that you compare fine-tuned LLMs of
  different sizes against zero-shot and heuristic baselines on a standardized
  protocol.

- **Section II (Related Work)** is solid. Consider adding a short paragraph
  on **LLM tool-calling / function-calling** literature (ToolLLM, Gorilla,
  BFCL) since your executive is essentially a specialized tool-caller.

- Add a **Discussion** subsection or paragraph in Section V addressing:
  - Why heuristics achieve high tool accuracy but low exact match (they can't
    do motion; they always default to INTERACT).
  - Why zero-shot 7B hallucinates motion actions when it should INTERACT
    (visible in the confusion matrix).
  - Scaling: 7B-FT vs 3B-FT gap is small — comment on whether 3B is
    sufficient for deployment on edge devices.

- **Conclusions** (currently empty): Write 1 paragraph summarizing results and
  1 paragraph on limitations + future work (real-hardware deployment, larger
  models, multimodal input, online learning from user feedback).

---

## 7. Quick-Reference: File Locations

| What | Path |
|---|---|
| Benchmark summary CSV | `evaluation/eval_outputs/paper_benchmark_run001/summary_all.csv` |
| Benchmark full JSON | `evaluation/eval_outputs/paper_benchmark_run001/summary_all.json` |
| Context breakdown CSV | `evaluation/eval_outputs/paper_benchmark_run001/context_breakdown.csv` |
| Confusion matrices CSV | `evaluation/eval_outputs/paper_benchmark_run001/confusion_matrices.csv` |
| Mistake samples (per model) | `evaluation/eval_outputs/paper_benchmark_run001/mistakes_*.jsonl` |
| Existing plot script | `evaluation/plots/make_offline_exec_figures.py` |
| Paper LaTeX source | `P_Rabiee_Copilot_IROS_2026/root.tex` |
| Paper bibliography | `P_Rabiee_Copilot_IROS_2026/root.bib` |
