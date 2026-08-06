---
name: hnia-pads-build
description: "Use this skill when building, testing, or extending the Pause-Aware Depth Scheduling (PADS) research system — a CPU-only, edge-deployed conversational AI mechanism combining self-speculative early-exit decoding with pause-time predictive prefetching. Trigger this skill for any task involving: llama.cpp/GGUF pipeline setup, LayerSkip-style early-exit reproduction, dialogue-act classifier training, turn-taking predictor integration, the Go/No-Go feasibility tests, or benchmarking (TTFT, tokens/sec, RAM, energy, acceptance rate) on the target Dell Latitude 5490 hardware. Do not use this skill to build a generic chatbot, a classifier-based LLM router, or a full-duplex GPU dialogue system — those are explicitly out of scope (see Non-Goals)."
---

# HNIA / PADS Build Skill

## 0. Read this first: what you are building and what you are NOT building

You are building a **narrow, falsifiable systems research artifact**, not a product. The one-sentence contribution is:

> Use the natural pause before a human finishes speaking (200–500ms) as free time to speculatively extend a self-speculative early-exit LLM to full depth, so reasoning-layer latency is partly hidden inside conversational silence — evaluated honestly on CPU-only, memory-bandwidth-bound hardware (no discrete GPU).

**Do NOT:**
- Build a classifier-based router between "a small model" and "a large model" as two separate models. This is a solved, crowded problem (RouteLLM, MixLLM) and is explicitly not the contribution.
- Attempt to "hand off" KV-cache between two differently-sized models. This is technically invalid — KV-caches are tied to a model's own hidden dimension and layer count. Depth extension must happen **within one model** (early layers → later layers of the same network), following the LayerSkip self-speculative pattern.
- Train a foundation model from scratch. Start from released checkpoints (e.g., Meta's LayerSkip-recipe Llama checkpoints) and do lightweight continued fine-tuning/LoRA only.
- Report any number that wasn't measured on the actual target hardware (Dell Latitude 5490, 16GB RAM, no discrete GPU). Cloud GPU is for training only, never for reported inference/latency/energy numbers.
- Skip the Go/No-Go tests in §2. They exist to falsify the core premise cheaply, in days, before deep implementation investment. If asked to "just start building the full system," push back and run these first.

## 1. Environment setup

```bash
# llama.cpp + GGUF pipeline
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build && cmake --build build --config Release   # CPU build; no CUDA/Metal flags on the Latitude 5490
pip install huggingface_hub

# Model acquisition — start from released LayerSkip checkpoints, not from-scratch training
# See: https://github.com/facebookresearch/LayerSkip
# Convert to GGUF only after fine-tuning is complete, quantize LAST:
python convert_hf_to_gguf.py <model_dir> --outtype f16
./build/bin/llama-quantize model-f16.gguf model-Q4_K_M.gguf Q4_K_M
```

Always quantize down from an F16 GGUF, never from an already-quantized file (compounds precision loss).

## 2. Go/No-Go tests — run these BEFORE building the full pipeline

Implement each as a small, independent, throwaway script. Do not proceed to §3 until all seven have a documented result (pass, fail, or "failed → pivoted, see note").

| # | Test | Command/approach | Kill signal |
|---|---|---|---|
| 1 | Bandwidth-vs-compute check | Run quantized 7–9B GGUF model, vary `--threads` 1→8 (llama-cli), plot tokens/sec | Flatlines past 4–5 threads → bandwidth-bound; note this and consider a smaller model |
| 2 | Real pause-duration check | Extract pause durations from Switchboard/CallHome corpus; compare to measured per-token decode time on this hardware | Pauses shorter than one meaningful speculative-depth step → redesign timing assumptions |
| 3 | Off-the-shelf acceptance rate | Run a public LayerSkip checkpoint unmodified on conversational-style prompts (`--generation_strategy self_speculative`), measure acceptance rate | Too low even before quantization damage → flag before custom training begins |
| 4 | Thermal stability check | 30-minute sustained inference loop; log `sensors`/`turbostat` temp and frequency | Significant throttling after N minutes → build warm-up + discard-first-runs into the benchmark protocol permanently |
| 5 | RAM budget check | Load intended model(s) at intended quantization; measure peak RSS (`/usr/bin/time -v` or `psutil`) with OS running normally | Doesn't fit in 16GB with headroom → shrink model size before adding engineering complexity |
| 6 | Energy tooling check | Try `turbostat` / `powertop` / RAPL sysfs on this exact machine | Reports nothing usable → switch to USB in-line power meter fallback, note this in the methodology section |
| 7 | Fresh literature scan | Search: "pause-aware early exit LLM", "predictive prefetch layer skipping conversational", "speculative decoding conversational pause" | Already published → reposition framing before writing further code |

Log every result (pass/fail + numbers) in `experiments/go_no_go_results.md`. This file is a required artifact, not optional documentation.

## 3. Build order (do not reorder)

1. **Safe-core pipeline first.** Get plain self-speculative early-exit decoding working and benchmarked on this hardware before touching turn-taking or pause-time triggering. This is the fallback result — it must work independently.
2. **Baselines, reproduced locally, not cited from other papers:**
   - Plain (non-speculative) decoding
   - Standard two-model speculative decoding
   - Plain cascading (small model decides → large model reprocesses from scratch)
   - LayerSkip's own published configuration, reproduced on this hardware
3. **Dialogue-act exit policy.** Train a lightweight classifier (on Switchboard-DAMSL or MultiWOZ, not from-scratch data collection) that predicts shallow-vs-deep need from a partial utterance. Compare against the standard token-confidence exit criterion.
4. **Only after 1–3 are stable and benchmarked:** integrate a CPU-capable turn-taking predictor (VAP-style) and implement the pause-time trigger logic (PADS proper, the stretch layer).
5. **Correctness check, mandatory:** verify the speculative branch, when discarded, produces output identical in distribution to non-speculative decoding. This is inherited from standard speculative decoding's correctness guarantee — do not weaken it for convenience.

## 4. Trigger policy implementation notes

- Use a **conservative, asymmetric threshold**: only trigger pause-time depth extension when both the turn-ending probability AND the deep-reasoning-need probability are high-confidence. Being wrong should be cheap; being right should be common. Tune for this asymmetry, not for raw accuracy.
- Pin the turn-taking predictor, dialogue-act classifier, and generation process to separate CPU cores (`taskset`) to avoid the three components starving each other for the same cores — profile with `perf` before concluding the architecture itself is the bottleneck.
- Log every trigger decision (fired / not fired / discarded) with its outcome, for later acceptance-rate and false-trigger-rate analysis.

## 5. Benchmarking requirements (non-negotiable for any reported number)

- Fixed CPU governor (disable dynamic frequency scaling variability where possible), no competing background load during measurement runs.
- Multiple seeds/runs; report mean ± confidence interval, never a single number.
- Warm-up period before every timed run; discard the first few runs per the thermal-stability findings from Go/No-Go #4.
- Every configuration logs: TTFT, tokens/sec, peak RAM, acceptance rate, and energy (RAPL/turbostat, or USB power-meter fallback).
- Store raw logs, not just summary tables, in `experiments/results/` — reproducibility requires the raw numbers to be re-aggregable.

## 6. Repository layout (suggested)

```
/experiments/
    go_no_go_results.md
    results/                # raw benchmark logs, one subdir per configuration
/models/
    checkpoints/            # fine-tuned LayerSkip-derived checkpoints (pre-GGUF)
    gguf/                   # quantized GGUF exports
/src/
    turn_taking/            # VAP-style predictor
    dialogue_act/           # classifier training + inference
    trigger_policy/         # pause-time trigger logic
    eval/                   # benchmarking harness, metric logging
/docs/
    (this project's Report, PRD, and reading list — kept alongside the code, not just in the PPT)
```

## 7. When something fails

- A failed Go/No-Go test is a **result**, not a blocker to hide. Document it in `go_no_go_results.md` with the pivot decision, and continue.
- If the stretch layer (pause-time triggering) does not show a measurable gain by the internal month-4 checkpoint (see Report §9, PRD §18), stop iterating on it and finalize the safe-core result as the reported contribution, with the stretch-layer attempt written up honestly as a limitation/negative result.
- Never silently drop a baseline comparison because it's inconvenient to reproduce — a missing baseline is a red flag to any reviewer and must be flagged to the human team member, not worked around.
