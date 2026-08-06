# HNIA → PADS: Detailed Project Report

**Project:** Hierarchical Native Interaction Architecture — Pause-Aware Depth Scheduling (PADS)
**Course:** Open Lab I & II (23ECE381 / 23EAC381)
**Version:** 1.0
**Target hardware:** Dell Latitude 5490 (Intel 8th-gen CPU, Intel UHD 620 iGPU, 16 GB RAM, no discrete GPU) + optional rented/free-tier cloud GPU for training only
**Status:** Research-locked, pre-implementation

---

## 1. Executive Summary

The original HNIA proposal (interaction layer + reasoning layer, routed by task complexity) is a **vision document**: it describes a category of system, not a checkable claim. Categories in this exact space are already crowded — LLM routing/cascading (RouteLLM, MixLLM, Lookahead routing), self-speculative early-exit decoding (LayerSkip, CLaSp, SWIFT, ConfLayers, KnapSpec), and full-duplex spoken dialogue (Moshi) all exist, are published, and are well cited. Submitting the original framing to any serious venue would read as a re-implementation.

After a structured pre-mortem and two rounds of refinement, the project is now locked around one falsifiable research bet:

> **Pause-Aware Depth Scheduling (PADS):** use the natural silence before a human finishes a conversational turn (200–500 ms) as free wall-clock time to speculatively begin the expensive part of computation (deep reasoning-layer inference, via self-speculative early exit) — before the user has even finished speaking — so that by the time the turn actually ends, some or all of the reasoning cost is already paid for, hidden inside a pause the user was going to leave anyway.

This fuses two independently mature and published techniques — predictive turn-taking/prefetching and self-speculative early-exit decoding — in a combination not found in the literature reviewed for this project. It is scoped with an explicit **safe core** (guaranteed, smaller, still-publishable result) and a **stretch layer** (the pause-time fusion itself), so the project cannot end with nothing to show even if the ambitious half fails.

---

## 2. Why the Original HNIA Framing Was Rejected

The uploaded HNIA documents (Executive Summary, System Architecture Specification, PRD v0.1) describe:

- A modular interaction/reasoning/memory/deployment split
- Escalation from a small conversational model to a larger reasoning model based on task complexity
- Distillation, quantization-aware training, long-context scaling, and memory compression as parallel "research tracks"

Every one of these, taken individually, is real, active, and already well-served by existing literature (see §3). None of them, described at this level of generality, constitutes a contribution a reviewer at IEEE Transactions, MLSys, or a comparable venue would accept — the language throughout the source documents ("remains an open question," "to be determined," "will be investigated") is itself diagnostic of a vision document rather than a research claim.

**Lesson carried forward:** every deliverable from this point on states one falsifiable sentence as its contribution, with the mechanism named, before any system description.

---

## 3. Literature Positioning (Why PADS, Specifically)

### 3.1 LLM routing / cascading — crowded, not the differentiator
RouteLLM [1], MixLLM [2], Lookahead Routing [3], and a 2026 survey on routing strategies [4] all address "send simple queries to a small model, hard queries to a large model." This is the literal shape of HNIA's original interaction/reasoning split. **Conclusion: do not build a classifier-based router as the headline contribution — it has been done multiple times, on production-scale systems, with rigorous evaluation already.**

### 3.2 Self-speculative early-exit decoding — the real foundation
LayerSkip [5] (ACL 2024, Meta) trains a single model with layer dropout and a shared early-exit loss, so early transformer layers can draft tokens that later layers verify **using the same KV-cache** — no second model, no cache-compatibility problem. Follow-ups (CLaSp, SWIFT, ConfLayers, KnapSpec) [6] refine which layers to skip and how. **This is the mechanism HNIA's "interaction vs reasoning" distinction should map onto** — not two separately trained models (which have incompatible KV-cache shapes and cannot "hand off" state to each other, a flaw in the project's earlier framing).

### 3.3 On-device / edge LLM serving — establishes the hardware angle is real, but also crowded
Surveys and systems on memory-aware offloading (FlexInfer), distributed home-cluster inference (prima.cpp) [7], energy-aware serving (EnerInfer) [8], and a direct empirical study asking whether CPUs can beat GPUs for on-device inference [9] confirm edge/CPU deployment is an active, legitimate research area — but memory-pressure-aware serving and CPU-vs-GPU characterization are themselves already partially covered, so they are supporting context, not the headline claim.

### 3.4 Full-duplex spoken dialogue and predictive turn-taking — the second half of the fusion
Moshi [10] demonstrates real-time full-duplex dialogue via a dual-stream architecture, but requires a dedicated neural audio codec and is evaluated on GPU-class hardware. Separately, predictive/prefetching techniques already exist for hiding latency across the pause boundary — Google's Personalized Predictive ASR [11] speculatively executes downstream processing before the final end-of-turn is confirmed, and lightweight CPU-capable turn-taking predictors (VAP, Krisp's model) [12] already run in real time on CPU.

### 3.5 The identified gap
No source reviewed combines **(a)** predictive prefetching across the pause boundary with **(b)** early-exit self-speculative *depth* extension, and no source reviewed characterizes early-exit self-speculative decoding specifically on **CPU-only, memory-bandwidth-bound consumer laptop hardware** rather than GPU. Both gaps are real, checkable, and matched to the Latitude 5490 constraint rather than fighting it.

---

## 4. The Core Research Bet: Pause-Aware Depth Scheduling (PADS)

### 4.1 Mechanism

1. A lightweight, CPU-capable turn-taking predictor (VAP-style) continuously estimates, from the partial user utterance, the probability that the turn is about to end.
2. A lightweight dialogue-act classifier, running on the same partial utterance, estimates whether the eventual response will need deep reasoning (analytical, coding, planning) or can be served from a shallow exit (greeting, acknowledgement, simple factual recall).
3. If both signals cross a calibrated confidence threshold **before** the turn actually ends, the system begins extending computation to full model depth *during the pause* — i.e., triggers the "verification" half of self-speculative early-exit decoding speculatively early, rather than waiting for the turn to complete.
4. If the prediction is confirmed at actual end-of-turn, the deep computation is already partially or fully done — the perceived latency is reduced by exactly the amount of pause time successfully exploited.
5. If the prediction is wrong (user keeps talking, or it was a false trigger), the speculative branch is discarded, following the same accept/reject logic already proven safe in standard speculative decoding — with an asymmetric, conservative trigger threshold so that being wrong is cheap.

### 4.2 Two-tier scoping

| Tier | Contribution | Status if achieved | Status if it fails |
|---|---|---|---|
| **Safe core** | First systematic characterization of self-speculative early-exit decoding (LayerSkip-style) on CPU-only, memory-bandwidth-bound consumer hardware, with a dialogue-act-driven exit policy compared against standard token-confidence exit | Solid, publishable (EdgeSys/MLSys/IEEE Access-tier) contribution on its own | Reframe as an honest negative/limiting result: "why GPU-derived early-exit gains do not transfer to CPU-bound inference" — still publishable |
| **Stretch layer** | Pause-time depth prefetching (PADS proper): hiding reasoning latency inside human conversational silence | Extraordinary, fusion contribution, strong candidate for a top-tier submission | Falls back cleanly onto the safe core; reported as a documented limitation, not a project failure |

### 4.3 Why this satisfies "extraordinary, not common"
It does not invent a new deep-learning architecture (too large a bet for two semesters) and does not merely re-badge an existing routing system (too common). It combines two already-validated, separately mature techniques in a way that is specific to human conversational timing and to CPU-bound hardware — both of which are under-explored precisely because most speculative-decoding research assumes GPU idle cycles are the resource being exploited, not human pause time.

---

## 5. Pre-Mortem: Full Risk Analysis

### 5.1 Mechanism-level risks
- **Acceptance rate collapse** under aggressive quantization (needed for 16 GB RAM) — shallow-exit predictions may disagree with full-depth output often enough that little computation is actually reused.
- **Memory-bandwidth-bound regime**: CPU/iGPU decoding is typically bandwidth-bound, not compute-bound. If true here, "extra idle compute during the pause" has nothing useful to exploit — the entire premise weakens.
- **Core contention**: VAD + dialogue-act classifier + speculative deep decoding running concurrently on a handful of CPU cores may saturate them, eating the very pause time being exploited.
- **Wrong-turn aborts**: a mispredicted end-of-turn burns compute on a discarded speculative branch; if frequent, net latency gets worse, not better.

### 5.2 Training/adaptation risks
- LayerSkip's training recipe (layer dropout + shared early-exit loss) needs real training compute; reproducing it on limited/free-tier cloud GPU sessions may not converge to comparable early-exit accuracy.
- The dialogue-act classifier needs labeled or synthetic conversational data not available off the shelf; building this could become its own multi-month subproject.
- Precision mismatch: calibrating during bf16 training but deploying 4-bit GGUF may not transfer the exit behavior correctly.

### 5.3 Hardware-specific risks
- 16 GB may not hold reasoning model + interaction/exit path + classifier + KV caches simultaneously, forcing swap and producing misleading latency numbers.
- Thermal throttling on a business laptop under sustained load can make back-to-back benchmark runs non-reproducible.
- RAPL/energy-measurement tooling may not expose clean readings on this exact BIOS/kernel combination, threatening a planned evaluation metric.

### 5.4 Measurement/methodology risks
- Testing with scripted prompts instead of real conversational audio leaves the core pause-timing premise unverified.
- Uncontrolled background OS/browser load confounds before/after latency comparisons.
- Weak baselines (comparing only to "no method" instead of to reproduced standard speculative decoding, plain cascading, and LayerSkip's own numbers) will not satisfy reviewers.

### 5.5 Novelty/positioning risks
- This space moves fast; a competing group could publish the same fusion within the six-month window.
- A reviewer could reasonably judge the fusion "incremental" — two known techniques combined is a real, non-trivial risk regardless of execution quality.
- The safe-core fallback itself could be scooped (adjacent CPU-vs-GPU inference studies already exist).

### 5.6 Execution risks
- The build requires custom early-exit training, llama.cpp/GGUF modification, a trained classifier, and rigorous benchmarking — a lot of distinct skill for a small team in two semesters.
- Reliance on free-tier cloud GPU sessions (rather than a reserved, budgeted allocation) risks losing days of training progress to interruptions.
- Review-checkpoint mismatch: if the stretch layer isn't demo-able by a fixed Open Lab review date, the team may be forced to present partial/negative results at a checkpoint not built for that framing.

### 5.7 Publication-timeline risks
- Six months is a research timeline, not a review-cycle timeline; "failed after 6 months" may really mean "not yet accepted."
- Venue mismatch (submitting a systems/latency contribution to a theory-focused venue, or vice versa) causes avoidable desk rejection.

### 5.8 Most likely first failure point
Of all risks above, the two most likely to bite **early and cheaply, if tested for** are: (a) the CPU/iGPU regime being memory-bandwidth-bound rather than compute-bound, leaving nothing for pause-time compute to exploit; and (b) real human pause durations being too short relative to a meaningful speculative-depth step, invalidating the timing premise before any model work begins. Both are addressed by Go/No-Go tests #1 and #2 below, run in week one.

---

## 6. Mitigations (Mapped to Each Risk Category)

| Risk category | Mitigation |
|---|---|
| Acceptance collapse | Start with a fixed, empirically chosen exit layer before any learned/adaptive threshold; add adaptivity only once the fixed version is proven |
| Bandwidth-bound regime | Reframe as a legitimate characterization result if confirmed; shrink the reasoning model (3B instead of 7–9B) to test whether a smaller model shifts the regime back toward compute-bound |
| Core contention | Pin VAD / classifier / generation to separate cores (`taskset`); profile with `perf` before attributing slowdown to the architecture |
| Wrong-turn aborts | Conservative, asymmetric trigger threshold — speculate only when confidently cheap to be wrong |
| Training doesn't transfer | Start from Meta's released LayerSkip checkpoints; do lightweight continued fine-tuning/LoRA only, not from-scratch training |
| No dialogue-act data | Use existing labeled corpora (Switchboard-DAMSL, MultiWOZ) instead of collecting from zero |
| Precision mismatch | Fake-quantize during training/calibration to match deployment precision; measure the train→deploy gap early |
| RAM overflow | Drop model size first, before adding engineering complexity (disk offloading, layer splitting) |
| Thermal throttling | Standardize a warm-up period, discard first runs, report steady-state throttled numbers as the real number — a recognized practice in edge-hardware evaluation, not a flaw to hide |
| RAPL unavailable | Fall back to an external USB power meter on the charger cable — accepted practice in embedded/edge papers |
| Untested pause premise | Use a real conversational audio corpus (Switchboard/CallHome) for pause statistics, not scripted prompts |
| Confounded benchmarking | Fixed CPU governor, no background load, multiple seeds, report mean ± confidence interval |
| Weak baselines | Always compare against reproduced standard speculative decoding, plain cascading, and LayerSkip's own numbers on this hardware |
| Getting scooped | Post an early arXiv preprint once the safe core is solid; run a biweekly literature scan (10 minutes, same search queries) |
| "Incremental" verdict | Write the paper so the safe-core sentence is true regardless of how the stretch goal lands |
| Skill/execution gap | Sequence: safe-core pipeline first, stretch fusion second — never let the ambitious half block a demoable checkpoint |
| Compute budget risk | Reserve and pre-budget actual paid cloud GPU hours; checkpoint training frequently |
| Publication timeline | Pick the target venue now and work backward from its real deadline; two-tier submission strategy (workshop for safe core, top venue for full fusion); internal month-4 checkpoint to decide reframe-vs-continue |

---

## 7. Go/No-Go Test Plan (Weeks 1–4)

| # | Test | Method | Kill signal | Action if failed |
|---|---|---|---|---|
| 1 | Bandwidth-vs-compute check | Quantized 7–9B model in llama.cpp, vary threads 1→8, plot tokens/sec | Throughput flatlines past 4–5 threads | Confirms bandwidth-bound regime — pivot to characterization framing, try smaller model |
| 2 | Real pause-duration check | Pause statistics from Switchboard/CallHome vs. measured per-step decode time on this hardware | Pauses shorter than one meaningful speculative-depth step | Redesign timing assumptions, not just tune parameters |
| 3 | Off-the-shelf acceptance rate | Public LayerSkip checkpoint, conversational-style prompts | Acceptance rate too low to matter, even pre-quantization | Told cheaply before months of custom training |
| 4 | Thermal stability check | 30-minute sustained inference loop, log CPU freq/temp | Significant throttling after N minutes | Fix benchmark protocol now (warm-up, discard-first-runs) |
| 5 | RAM budget check | Load intended models at intended quantization, measure peak RSS | Doesn't fit in 16 GB with headroom | Revisit model-size decision immediately |
| 6 | Energy tooling check | Try RAPL / `turbostat` / `powertop` on this exact machine | Reports nothing usable | Switch to USB power-meter fallback now |
| 7 | Fresh scoop check | Targeted literature search for the exact fusion | Already published | Reposition framing before writing, not after |

---

## 8. Hardware & Compute Plan

- **Primary development/inference hardware:** Dell Latitude 5490, 16 GB RAM, Intel 8th-gen CPU, Intel UHD 620 iGPU, no discrete GPU. All final latency/energy/memory numbers reported from this machine.
- **Model formats:** GGUF via llama.cpp; Q4_K_M as the default working precision, Q5/Q6/Q8 and F16 as calibration references for the QAT/quantization ablation.
- **Model sizes:** Interaction/shallow-exit path ≤ 2B parameters equivalent; reasoning/full-depth path in the 3B–9B range, sized against the RAM-budget check (Go/No-Go #5) rather than assumed.
- **Cloud GPU role:** training and fine-tuning only (continued pretraining, LoRA adaptation of the LayerSkip recipe, dialogue-act classifier training) — never used for the reported inference/latency numbers, to keep the hardware story honest and reproducible on commodity hardware.
- **Cloud budget:** a specific, pre-reserved, paid allocation (not solely free-tier), with frequent checkpointing so a session interruption costs minutes, not days.

---

## 9. Publication Strategy

1. **Safe core → fast-turnaround workshop** (e.g., NeurIPS Efficient ML workshop, ES-FoMo, an EdgeAI-focused workshop) as an early, low-risk, citable result — targeted for submission once Go/No-Go tests and the safe-core pipeline are stable (approx. end of Semester 1).
2. **Full fusion (PADS) → systems venue with longer runway** (MLSys, ACM/IEEE EdgeSys/SEC, or an IEEE Transactions outlet such as IoT Journal or Mobile Computing) — targeted for Semester 2, contingent on the stretch layer showing a real, measured signal by the internal month-4 checkpoint.
3. **arXiv preprint** posted as soon as the safe-core result is solid, to timestamp the contribution and invite early feedback ahead of any competing publication.
4. **Explicit month-4 internal checkpoint**: if the stretch layer has not shown a real signal by then, consciously reframe as a documented negative/limitation result rather than silently extending the timeline.

---

## 10. Timeline (Semester 1 & 2, Gated by Go/No-Go)

**Semester 1**
- Weeks 1–4: Literature review finalization; Go/No-Go tests #1–7 (§7); environment setup (llama.cpp build, GGUF pipeline, hardware profiling tooling).
- Weeks 5–8: Safe-core pipeline — reproduce LayerSkip-style early exit on the target hardware; establish baseline speculative-decoding and cascading comparisons.
- Weeks 9–12: Dialogue-act-driven exit policy; comparison against token-confidence exit; safe-core benchmarking (TTFT, tokens/sec, RAM, energy).
- Weeks 13–16: Intermediate report and Open Lab I review; safe-core result finalized as fallback-safe; begin stretch-layer prototyping (turn-taking predictor integration).

**Semester 2**
- Weeks 1–6: PADS stretch layer — pause-time speculative depth extension; integration of turn-taking + dialogue-act signals into the trigger policy.
- Weeks 7–10: Full benchmarking of PADS against safe core and all baselines; month-4-equivalent internal checkpoint decision (continue fusion vs. reframe as limitation).
- Weeks 11–14: Hardware demonstration; final benchmark suite; energy/thermal-aware reporting.
- Weeks 15–16: Final report, workshop/venue submission, Open Lab II review and demonstration.

---

## 11. Goals and Success Criteria

**Functional**
- Working conversational pipeline on the Latitude 5490, fully offline at inference time.
- Reproducible early-exit self-speculative decoding pipeline with measured acceptance rates.
- A trigger policy (dialogue-act-driven) compared quantitatively against a token-confidence baseline.

**Performance (indicative, to be finalized against Go/No-Go results)**
- Measurable reduction in time-to-first-token attributable specifically to pause-time depth extension, or a clearly documented negative result explaining why not.
- Full reporting of tokens/sec, peak RAM, and energy (RAPL or USB-meter fallback) across all compared methods.

**Research**
- A safe-core contribution defensible on its own at a workshop/EdgeSys/IEEE-Access tier.
- A clearly stated, falsifiable stretch contribution (PADS) attempted with honest reporting regardless of outcome.
- A related-work section demonstrating awareness of the crowded routing/cascading and self-speculative-decoding literature, positioning HNIA/PADS precisely against it.

---

## 12. References

[1] I. Ong et al., "RouteLLM: Learning to Route LLMs with Preference Data," arXiv:2406.18665, 2024.
[2] "MixLLM: Dynamic Routing in Mixed Large Language Models," arXiv:2502.18482, 2025.
[3] "Lookahead Routing for Large Language Models," arXiv:2510.19506, 2025.
[4] "Doing More with Less: A Survey on Routing Strategies for Resource Optimisation in LLM-Based Systems," arXiv:2502.00409, 2025.
[5] M. Elhoushi et al., "LayerSkip: Enabling Early Exit Inference and Self-Speculative Decoding," ACL 2024, arXiv:2404.16710.
[6] "Component-Aware Self-Speculative Decoding in Hybrid Language Models" (surveys CLaSp, SWIFT, ConfLayers, KnapSpec), arXiv:2605.01106, 2026.
[7] "Prima.cpp: Fast 30–70B LLM Inference on Heterogeneous and Low-Resource Home Clusters," arXiv:2504.08791, 2025.
[8] "EnerInfer: Energy-Aware On-Device LLM Inference," arXiv:2606.23001, 2026.
[9] "Challenging GPU Dominance: When CPUs Outperform for On-Device LLM Inference," arXiv:2505.06461, 2025.
[10] A. Défossez et al., "Moshi: A Speech-Text Foundation Model for Real-Time Dialogue," Kyutai, arXiv:2410.00037, 2024.
[11] "Personalized Predictive ASR for Latency Reduction in Voice Assistants," arXiv:2305.13794, 2023.
[12] Krisp, "Audio-only, 6M-weight Turn-Taking Model for Voice AI Agents," 2025; "RESPOND: Responsive Engagement Strategy for Predictive Orchestration and Dialogue," arXiv:2603.21682, 2026.
[13] J. Lin et al., "AWQ: Activation-Aware Weight Quantization for On-Device LLM Compression and Acceleration," MLSys 2024.
[14] Z. Liu et al., "LLM-QAT: Data-Free Quantization Aware Training for Large Language Models," ACL Findings 2024.
[15] "Collaborative Learning of On-Device Small Model and Cloud-Based Large Model: Advances and Future Directions," arXiv:2504.15300, 2025.

*(Full IEEE-formatted reference list to be finalized in the PRD/PPT reference slide; DOIs to be added once specific paper versions are locked for citation.)*
