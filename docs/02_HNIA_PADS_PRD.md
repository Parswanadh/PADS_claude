# Product Requirements Document (PRD)

# Pause-Aware Depth Scheduling (PADS)
### (formerly: Hierarchical Native Interaction Architecture — HNIA)

**Version:** 1.0
**Status:** Research-locked, pre-implementation
**Project type:** Open Lab I & II Research Project
**Duration:** Two semesters
**Target hardware:** Dell Latitude 5490, 16 GB RAM, no discrete GPU (+ optional cloud GPU for training only)

---

## Table of Contents
1. Vision
2. Problem Statement
3. Research Goals
4. Success Criteria
5. Target Users / Audience
6. Scope
7. Non-Goals
8. Design Philosophy
9. System Overview
10. Functional Requirements
11. Non-Functional Requirements
12. Research Objectives
13. Technical Roadmap
14. Risk Register (Summary)
15. Evaluation Metrics & Baselines
16. Hardware & Compute Requirements
17. Deliverables
18. Publication Plan

---

## 1. Vision

Build and rigorously evaluate a single, falsifiable mechanism — **Pause-Aware Depth Scheduling (PADS)** — that hides the latency of deep conversational reasoning inside the natural silence of human speech, on hardware that has no dedicated GPU. The project is explicitly **not** a general conversational-AI platform; it is a narrow systems contribution with a safe fallback result and an ambitious stretch result, both scoped to be independently defensible.

## 2. Problem Statement

- **Routing/cascading between a small and large model is a solved, crowded research area** (RouteLLM, MixLLM, Lookahead Routing) — re-implementing it is not a contribution.
- **Self-speculative early-exit decoding (LayerSkip and successors) is proven but only characterized on GPU hardware.** Whether it helps at all on CPU/iGPU, memory-bandwidth-bound consumer laptops is an open, unanswered, and checkable question.
- **Predictive prefetching across conversational pauses is known** (Personalized Predictive ASR, VAP) but has not been combined with early-exit *depth* extension — i.e., using the pause to go deeper into the model, not just to pre-compute the next pipeline stage.
- **Prior HNIA framing assumed two separately trained models could "hand off" KV-cache state** — a technically invalid assumption, since KV-caches are tied to a model's own hidden dimension and layer count and are not interchangeable across differently sized models.

## 3. Research Goals

1. Characterize self-speculative early-exit decoding's real behavior on CPU-only, memory-bandwidth-bound edge hardware (the Latitude 5490), which is not covered in existing GPU-centric literature.
2. Compare a **dialogue-act-driven, turn-level exit policy** against the standard **token-confidence exit policy** used in existing early-exit work.
3. Attempt the stretch fusion — **pause-time speculative depth extension** — as a genuinely novel combination, with an honest, pre-committed fallback to (1)+(2) if it does not produce a measurable gain.
4. Produce a reproducible, hardware-grounded evaluation suite (latency, throughput, memory, energy) usable by future Open Lab cohorts and by external reviewers.

## 4. Success Criteria

### Functional
- End-to-end offline conversational pipeline runs entirely on the Latitude 5490 at inference time.
- Self-speculative early-exit decoding reproduced and benchmarked on this hardware.
- Dialogue-act-driven exit policy implemented and compared quantitatively against token-confidence exit.
- Pause-time depth extension (PADS proper) implemented and benchmarked, or a documented negative result explaining why it did not produce a gain.

### Performance (targets, to be finalized after Go/No-Go tests — see Risk Register)
| Metric | Target | Notes |
|---|---|---|
| Time-to-First-Token (TTFT), safe core vs. plain decoding | Measurable, reported reduction or honest null result | Must be attributable specifically to the exit mechanism, not confounded by other factors |
| TTFT, PADS vs. safe core | Measurable reduction attributable to pause-time extension | Contingent on Go/No-Go test #2 (pause-duration feasibility) |
| Peak RAM | Fits within 16 GB with working headroom for OS + pipeline | Verified by Go/No-Go test #5 before model-size is finalized |
| Offline capability | 100% at inference time | Cloud used only for training/fine-tuning |
| Acceptance rate (self-speculative exit) | Reported honestly, whatever the number | A low number is a valid, reportable research finding, not a failure to hide |

### Research
- A safe-core result independently defensible at a workshop/EdgeSys/IEEE-Access tier, regardless of stretch-layer outcome.
- A related-work section demonstrating the routing/cascading and self-speculative-decoding space is understood and correctly positioned against.
- A reproducible benchmark artifact (code, configs, logged results) for both safe core and stretch layer.

## 5. Target Users / Audience

**Primary:** the project's own guide/evaluators (Open Lab I & II reviews), and — if submission proceeds — reviewers at the targeted workshop/venue.
**Secondary:** researchers and practitioners working on edge/on-device conversational AI, CPU-bound LLM serving, and self-speculative decoding, who would use the benchmark artifact or reproduce the characterization.

## 6. Scope

**Included**
- Environment setup: llama.cpp / GGUF pipeline on the Latitude 5490.
- Reproduction of LayerSkip-style self-speculative early exit (from released checkpoints, with lightweight fine-tuning, not training from scratch).
- Dialogue-act classifier (trained on existing labeled corpora, e.g. Switchboard-DAMSL/MultiWOZ).
- Turn-taking predictor integration (VAP-style, CPU-capable).
- Pause-time depth-extension trigger logic (PADS proper).
- Full benchmark suite: TTFT, tokens/sec, peak RAM, energy (RAPL/turbostat or USB power-meter fallback), acceptance rate.
- Go/No-Go test suite executed and documented in Weeks 1–4.

**Explicitly excluded from this scope** (see §7)

## 7. Non-Goals

HNIA/PADS is **not** attempting to:
- Train a new foundation model from scratch.
- Build a general-purpose, commercial-grade conversational assistant.
- Reproduce or compete with Moshi's full-duplex GPU architecture.
- Build a new LLM router/classifier system as the headline contribution (routing is supporting infrastructure at most, not the claim).
- Guarantee a top-tier acceptance — the project targets a rigorous, honestly reported result, with venue fit decided based on what the result actually shows.

## 8. Design Philosophy

1. **One falsifiable claim, stated first**, before any system description.
2. **Two-tier scoping**: a safe, guaranteed-defensible core, and a stretch layer that is additive, not load-bearing.
3. **Test the premise before building the system** — Go/No-Go tests run before deep implementation investment.
4. **Hardware constraints are the research niche, not an obstacle** — the Latitude 5490's CPU-only, memory-bandwidth-bound profile is the reason the research question is interesting.
5. **Honest negative results are valid deliverables**, pre-committed to at the design stage, not improvised after a disappointing result.
6. **Reproducibility over scale** — every reported number must be regenerable from documented configs on the same hardware.

## 9. System Overview

```
User speech (partial utterance, streaming)
        │
        ├──▶ Turn-taking predictor (VAP-style, CPU) ──▶ P(turn ending soon)
        │
        └──▶ Dialogue-act classifier (lightweight) ──▶ shallow-serve vs. deep-reasoning signal
                        │
                        ▼
        Trigger policy (conservative, asymmetric threshold)
                        │
        ┌───────────────┴────────────────┐
        ▼                                 ▼
 Stay at shallow exit              Begin full-depth extension
 (LayerSkip-style early layers)    speculatively, during the pause
        │                                 │
        └────────────── merge ────────────┘
                        │
                        ▼
         Verify against actual end-of-turn;
         accept / discard speculative branch
                        │
                        ▼
              Response generation (streaming)
```

This diagram supersedes the original HNIA "interaction layer / reasoning layer as two separate models" diagram — depth (shallow vs. full exit within one model) replaces model-switching.

## 10. Functional Requirements

The system shall:
- Accept streaming partial-utterance input and run turn-taking + dialogue-act inference on it continuously.
- Trigger speculative full-depth computation only above a calibrated, conservative confidence threshold.
- Correctly discard mispredicted speculative branches without corrupting the final output (output must be identical in distribution to non-speculative decoding — the correctness guarantee inherited from speculative decoding literature).
- Run entirely offline on the Latitude 5490 at inference time.
- Log every run's TTFT, tokens/sec, peak RAM, acceptance rate, and (where available) energy draw, for every configuration compared.

## 11. Non-Functional Requirements

| Requirement | Priority |
|---|---|
| Reproducibility (fixed seeds, documented configs, controlled benchmarking environment) | Highest |
| Correctness (speculative branch never changes output distribution) | Highest |
| Offline capability at inference | High |
| Latency (TTFT reduction where the mechanism claims it) | High |
| Memory footprint within 16 GB | High |
| Energy measurement availability | Medium (fallback plan required) |
| Extensibility for future Open Lab cohorts | Medium |

## 12. Research Objectives

1. Reproduce and characterize self-speculative early-exit decoding on CPU-only hardware.
2. Compare token-confidence vs. dialogue-act-driven exit policies.
3. Implement and evaluate pause-time depth extension (PADS).
4. Quantify acceptance rate, latency, memory, and energy trade-offs across all of the above.
5. Produce a rigorous related-work positioning distinguishing PADS from routing/cascading and from GPU-centric self-speculative decoding work.

## 13. Technical Roadmap

**Phase 1 — Foundations (Weeks 1–4):** Go/No-Go tests; llama.cpp/GGUF environment; hardware profiling tooling; literature finalization.
**Phase 2 — Safe core (Weeks 5–12):** Reproduce LayerSkip-style early exit; implement dialogue-act exit policy; baseline benchmarking against standard speculative decoding and plain cascading.
**Phase 3 — Intermediate checkpoint (Weeks 13–16):** Safe-core result finalized as fallback; Open Lab I review; begin stretch-layer prototyping.
**Phase 4 — Stretch layer (Semester 2, Weeks 1–6):** Turn-taking + dialogue-act-triggered pause-time depth extension.
**Phase 5 — Full evaluation (Weeks 7–10):** Complete benchmark suite; month-4-equivalent go/continue decision.
**Phase 6 — Finalization (Weeks 11–16):** Hardware demonstration; final report; submission.

## 14. Risk Register (Summary)

See the companion Detailed Report (§5–7) for the full pre-mortem. Top risks carried as active watch items:
- CPU/iGPU inference may be memory-bandwidth-bound, weakening the pause-time-compute premise (Go/No-Go #1).
- Real human pause durations may be shorter than one meaningful speculative-depth step (Go/No-Go #2).
- Acceptance rate may collapse under required quantization (Go/No-Go #3).
- 16 GB RAM may not fit the full pipeline simultaneously (Go/No-Go #5).
- Reviewer verdict of "incremental fusion" is a standing risk regardless of execution quality — mitigated by the two-tier scoping and honest related-work positioning.

## 15. Evaluation Metrics & Baselines

**Metrics:** TTFT, tokens/sec, peak RAM, energy (RAPL/turbostat, fallback USB power meter), acceptance rate, exit-policy accuracy (dialogue-act vs. token-confidence).

**Baselines (must be reproduced on the same hardware, not cited from other papers' numbers):**
- Plain (non-speculative) decoding.
- Standard two-model speculative decoding.
- Plain cascading/routing (small model decides, large model re-processes from scratch).
- LayerSkip's own published configuration, reproduced locally.

## 16. Hardware & Compute Requirements

- **Inference hardware (all reported numbers):** Dell Latitude 5490, 16 GB RAM, Intel 8th-gen CPU, Intel UHD 620, no discrete GPU.
- **Model formats:** GGUF via llama.cpp, Q4_K_M default, F16/Q8/Q6/Q5 as calibration references.
- **Training/fine-tuning hardware:** cloud GPU (pre-budgeted, paid allocation preferred over free-tier), used only for LayerSkip continued fine-tuning/LoRA and dialogue-act classifier training — never for reported inference numbers.
- **Energy measurement:** RAPL/turbostat primary; USB in-line power meter as pre-planned fallback.

## 17. Deliverables

**Semester 1:** Literature review (PADS-positioned), this PRD, architecture spec, Go/No-Go test results, safe-core pipeline and benchmarks, Open Lab I review materials.
**Semester 2:** Stretch-layer implementation and benchmarks, month-4 checkpoint decision record, full evaluation suite, final report, submission-ready manuscript, Open Lab II demonstration.

## 18. Publication Plan

- Safe-core result → fast-turnaround workshop (NeurIPS Efficient ML / ES-FoMo / EdgeAI workshop), targeted end of Semester 1.
- Full PADS fusion → systems venue with longer runway (MLSys / ACM-IEEE EdgeSys or SEC / IEEE Transactions on Mobile Computing or IoT Journal), targeted Semester 2, contingent on the month-4 checkpoint showing a real signal.
- arXiv preprint posted once the safe-core result is solid.
- Explicit internal decision gate at month 4: continue stretch layer vs. reframe as documented limitation.
