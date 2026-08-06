# PPT Content Points — Open Lab I, First Review
### (Matches the 23ECE381/23EAC381 template structure exactly — fill directly into the template slides)

---

## Slide 1 — Title Slide

- **Title:** Pause-Aware Depth Scheduling (PADS): CPU-Only Edge Conversational Inference via Self-Speculative Early Exit
- *(Subtitle, optional):* formerly "Hierarchical Native Interaction Architecture (HNIA)" — reframed after literature positioning
- Team members / Reg. No. / TID — [fill in]
- Guide name — [fill in]
- Evaluators — [fill in]

---

## Slide 2 — Motivation / Problem Statement (ONE SLIDE ONLY)

**Problem (3 bullets):**
- Conversational AI on edge hardware (laptops/embedded devices with no discrete GPU) forces a choice between fast-but-shallow responses and slow-but-capable reasoning — existing systems don't recover the latency lost when escalating to deeper reasoning.
- Self-speculative early-exit decoding (e.g., LayerSkip) proves this escalation can be nearly free on GPUs, but has never been systematically characterized on CPU/iGPU, memory-bandwidth-bound consumer hardware.
- Human conversational pauses (200–500ms before a turn ends) are computational time that current systems simply leave unused, even though the system already has enough partial information to start deeper computation early.

**Why it matters (2 bullets):**
- Privacy-sensitive, offline, and cost-constrained deployments (robotics, embedded assistants, disconnected environments) cannot rely on cloud GPUs, so latency hiding must come from smarter use of existing CPU-only hardware and conversational timing, not more compute.
- If proven, this reframes "the pause" as a usable resource — analogous to how speculative decoding reframed idle GPU cycles as a usable resource.

**Applications after solved (1–2 bullets):**
- Faster, more natural offline conversational assistants on commodity/embedded hardware (laptops, Raspberry-Pi-class devices, robotics platforms).
- A reusable, hardware-grounded benchmarking methodology for future CPU-only speculative-decoding research.

---

## Slide 3 — Literature Survey (one slide per paper — duplicate this layout)

### Paper 1
- **PAPER TITLE:** LayerSkip: Enabling Early Exit Inference and Self-Speculative Decoding (Elhoushi et al., ACL 2024)
- **OBJECTIVE:** Speed up LLM inference by training a single model to support accurate early-layer exits, then verifying/correcting with the remaining layers — without a separate draft model.
- **METHODOLOGY:** Layer dropout (higher at later layers) during training + a shared early-exit loss across all layers; at inference, exit early to draft, continue through remaining layers to verify, reusing the same KV-cache.
- **INFERENCE (what we learned):** Depth-based self-speculation avoids the KV-cache incompatibility problem that would occur with two separately-sized models — this directly fixed a flawed assumption in our original architecture (that a small and large model could "hand off" state to each other).
- **How we apply it:** This is the literal mechanism our "interaction vs. reasoning layer" distinction is built on — not two models, but shallow vs. full depth of one model.

### Paper 2
- **PAPER TITLE:** RouteLLM: Learning to Route LLMs with Preference Data (Ong et al., 2024)
- **OBJECTIVE:** Route each query to a small or large LLM based on predicted query difficulty, to balance cost and quality.
- **METHODOLOGY:** Binary classifier trained on preference data (Chatbot Arena) predicting whether the large model would be preferred for a given query.
- **INFERENCE:** This is exactly the "interaction/reasoning escalation" pattern our original proposal described — and it's already a mature, well-evaluated research area with multiple follow-ups (MixLLM, Lookahead Routing). Building this as our headline contribution would not be novel.
- **How we apply it:** Cited as related work to explicitly position PADS as different from routing — PADS operates on model *depth*, triggered by *conversational timing*, not on model *selection*, triggered by query classification.

### Paper 3
- **PAPER TITLE:** Moshi: A Speech-Text Foundation Model for Real-Time Dialogue (Défossez et al., Kyutai, 2024)
- **OBJECTIVE:** Achieve real-time, full-duplex spoken dialogue (both parties can speak/listen simultaneously) with ~200ms latency.
- **METHODOLOGY:** A 7B text backbone (Helium) + a neural audio codec (Mimi) modeling user and system audio as parallel streams, removing explicit turn-taking.
- **INFERENCE:** Demonstrates the ceiling of what's possible with dedicated GPU-class hardware and a purpose-built audio codec — and confirms that this ceiling is not reachable on CPU-only edge hardware, motivating our narrower, hardware-honest scope (approximate latency-hiding within standard turn-taking, not full duplex).
- **How we apply it:** Cited as the upper bound / contrast case, not a system we are reproducing.

### Paper 4 (second/third paper — subsequent slide)
- **PAPER TITLE:** Personalized Predictive ASR for Latency Reduction in Voice Assistants (Google, 2023)
- **OBJECTIVE:** Reduce user-perceived latency by speculatively processing a preliminary transcript before the final end-of-turn is confirmed.
- **METHODOLOGY:** A secondary, lower-confidence endpoint threshold triggers speculative downstream execution; if the final transcript confirms the preliminary one, the pre-computed result is returned immediately.
- **INFERENCE:** This is the direct precedent for "using the pause productively" — but it prefetches a whole pipeline stage, not a specific model *depth*. Combining this idea with LayerSkip's depth-based speculation is the gap our project targets.
- **How we apply it:** Directly informs the PADS trigger-policy design (§ Conceptual Architecture).

*(Add a 5th slide for Prima.cpp / CPU-vs-GPU on-device inference paper if time allows — same OBJECTIVE/METHODOLOGY/INFERENCE format, focused on establishing the CPU/memory-bandwidth constraint as a real, evidenced research niche.)*

---

## Slide 4 — Summary of Literature Survey (table)

| Title | Problem Addressed | Methodology/Tools Used | Final Outcomes | Gaps Identified |
|---|---|---|---|---|
| LayerSkip (ACL 2024) | LLM inference latency | Layer dropout + shared early-exit loss + self-speculative decoding | Up to ~2x speedup on GPU (Llama models) | Never evaluated on CPU/iGPU, memory-bandwidth-bound hardware |
| RouteLLM (2024) | Cost/quality trade-off across model sizes | Preference-trained binary classifier router | Effective cost savings at production scale | Solved problem — not a novelty opportunity for us |
| Moshi (Kyutai, 2024) | Full-duplex spoken dialogue latency | 7B text backbone + neural audio codec, dual-stream | ~200ms real-time full-duplex on GPU | Requires dedicated GPU + custom audio codec; not CPU-feasible |
| Predictive ASR (Google, 2023) | Latency from waiting for end-of-turn confirmation | Speculative execution on preliminary transcript | Hides part of downstream latency | Prefetches pipeline stage, not model depth — gap we fill |
| Prima.cpp (2025) | Running large models on low-resource consumer hardware | Memory-pressure-aware distributed inference | 70B model runs locally at reduced memory pressure | Memory-yielding, not latency-hiding via conversational timing |

---

## Slide 5–6 — Conceptual Architecture / Block Diagram and Methodology (1–2 slides)

**Block diagram (describe for the diagram slide):**
```
User speech (streaming, partial) 
   → [Turn-taking predictor] + [Dialogue-act classifier]  (both CPU, lightweight)
   → Trigger policy (conservative, asymmetric threshold)
       → NO trigger: stay at shallow exit (early layers only)
       → TRIGGER: begin full-depth extension speculatively, during the pause
   → Merge at actual end-of-turn: accept confirmed branch / discard mispredicted branch
   → Streaming response generation
```

**Methodology (bullets):**
- Reproduce LayerSkip-style self-speculative early exit on target hardware (safe core) before adding any timing-based triggering.
- Build the dialogue-act classifier from existing labeled conversational corpora (Switchboard-DAMSL / MultiWOZ) — no from-scratch data collection.
- Integrate a CPU-capable turn-taking predictor (VAP-style) only after the safe core is benchmarked and stable.
- Implement the pause-time trigger as an additive stretch layer — the safe core must remain independently functional and reportable throughout.
- All correctness must match standard speculative decoding's guarantee: a discarded speculative branch never changes the final output distribution.

---

## Slide 7–10 — Circuit Diagram / Specifications of each block (max 4 slides)

**Block 1 — Reasoning/shallow-exit backbone**
- Base: LayerSkip-recipe checkpoint (e.g., Llama-family, publicly released), 3B–9B range — exact size finalized against the RAM budget test.
- Deployment format: GGUF via llama.cpp, Q4_K_M default; F16/Q8/Q6/Q5 kept as calibration references for the quantization ablation.
- Target device: Dell Latitude 5490, 16GB RAM, no discrete GPU.

**Block 2 — Turn-taking predictor**
- CPU-capable, lightweight (reference scale: ~6M parameters, per Krisp's published model), operates on streaming partial audio/text.
- Output: P(turn ending within next ~300ms).

**Block 3 — Dialogue-act classifier**
- Lightweight classifier trained on Switchboard-DAMSL / MultiWOZ labels.
- Output: shallow-serve vs. deep-reasoning-need signal, computed on the same partial utterance as Block 2.

**Block 4 — Trigger policy & benchmarking harness**
- Conservative, asymmetric threshold combining Blocks 2+3 outputs.
- Logged per-decision: fired/not-fired, confirmed/discarded, resulting latency.
- Benchmark harness metrics: TTFT, tokens/sec, peak RAM, acceptance rate, energy (RAPL/turbostat or USB power-meter fallback).

---

## Slide 11 — Workdone So Far and Work to be Completed (ONE SLIDE)

**Done:**
- Literature review completed and positioned (routing/cascading vs. self-speculative decoding vs. spoken-dialogue/turn-taking landscapes).
- Original HNIA architecture identified as technically flawed (KV-cache handoff between differently-sized models) and corrected.
- Core research bet locked: Pause-Aware Depth Scheduling (PADS), with explicit safe-core/stretch-layer scoping.
- Full pre-mortem risk analysis completed; Go/No-Go test suite designed (7 tests).
- PRD, architecture spec, and build skill/playbook finalized for implementation handoff.

**To be completed (next):**
- Execute all 7 Go/No-Go tests (Weeks 1–4) — bandwidth-vs-compute, pause-duration feasibility, off-the-shelf acceptance rate, thermal stability, RAM budget, energy tooling, fresh-literature scoop check.
- Build and benchmark the safe-core pipeline (self-speculative early exit + dialogue-act exit policy) on the Latitude 5490.
- Reproduce all required baselines locally (plain decoding, standard speculative decoding, plain cascading, LayerSkip's own config).

---

## Slide 12 — Timeline

**Semester 1**
- Weeks 1–4: Go/No-Go tests; environment setup (llama.cpp/GGUF); literature finalization.
- Weeks 5–8: Safe-core pipeline (early-exit reproduction) + baseline benchmarking.
- Weeks 9–12: Dialogue-act exit policy vs. token-confidence exit comparison.
- Weeks 13–16: Safe-core result finalized as fallback; Open Lab I review; begin stretch-layer prototyping.

**Semester 2**
- Weeks 1–6: PADS stretch layer — turn-taking + dialogue-act pause-time triggering.
- Weeks 7–10: Full benchmark suite; **internal month-4 go/no-go checkpoint** — continue fusion vs. reframe as documented limitation.
- Weeks 11–14: Hardware demonstration; final benchmarking; energy/thermal-aware reporting.
- Weeks 15–16: Final report; workshop/venue submission; Open Lab II review and demonstration.

**Pre-publication milestones (overlaid on the above):**
- End of Semester 1: safe-core result solid → post arXiv preprint → submit to fast-turnaround workshop (NeurIPS Efficient ML / ES-FoMo / EdgeAI workshop).
- Month-4 of Semester 2: go/no-go decision on stretch layer.
- End of Semester 2: full PADS result (or honest limitation writeup) → submit to systems venue with longer runway (MLSys / EdgeSys / SEC / IEEE Transactions on Mobile Computing or IoT Journal).

---

## Slide 13 — Goals (add if the template allows an extra slide, otherwise fold into Timeline slide)

- Deliver a working, fully offline, CPU-only conversational pipeline on the Latitude 5490.
- Deliver a rigorous, reproducible characterization of self-speculative early-exit decoding on CPU-only hardware (guaranteed contribution).
- Attempt the pause-time depth-extension fusion (PADS) as the stretch, extraordinary contribution — reported honestly regardless of outcome.
- Produce a submission-ready manuscript positioned precisely against the current routing/cascading and self-speculative-decoding literature.

---

## Slide 14 — References (IEEE format — stop here for Q&A)

[1] M. Elhoushi et al., "LayerSkip: Enabling Early Exit Inference and Self-Speculative Decoding," in *Proc. 62nd Annu. Meeting Assoc. Comput. Linguistics (ACL)*, 2024.

[2] I. Ong, A. Almahairi, V. Wu, W.-L. Chiang, T. Wu, J. E. Gonzalez, M. W. Mahoney, and I. Stoica, "RouteLLM: Learning to Route LLMs with Preference Data," *arXiv:2406.18665*, 2024.

[3] A. Défossez, L. Mazaré, M. Orsini, A. Royer, P. Pérez, H. Jégou, E. Grave, and N. Zeghidour, "Moshi: A Speech-Text Foundation Model for Real-Time Dialogue," *arXiv:2410.00037*, 2024.

[4] "Personalized Predictive ASR for Latency Reduction in Voice Assistants," *arXiv:2305.13794*, 2023.

[5] "Prima.cpp: Fast 30–70B LLM Inference on Heterogeneous and Low-Resource Home Clusters," *arXiv:2504.08791*, 2025.

[6] "Challenging GPU Dominance: When CPUs Outperform for On-Device LLM Inference," *arXiv:2505.06461*, 2025.

[7] J. Lin, J. Tang, H. Tang, S. Yang, W.-M. Chen, W.-C. Wang, G. Xiao, X. Dang, C. Gan, and S. Han, "AWQ: Activation-Aware Weight Quantization for On-Device LLM Compression and Acceleration," in *Proc. Mach. Learn. Syst. (MLSys)*, 2024.

[8] Y. Leviathan, M. Kalman, and Y. Matias, "Fast Inference from Transformers via Speculative Decoding," in *Proc. Int. Conf. Mach. Learn. (ICML)*, 2023.

*(Finalize page numbers/volume details for each entry once the exact cited version is locked; add entries 9+ as additional papers are incorporated during the literature review.)*

**— stop here for Q&A —**
