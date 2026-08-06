# Literature Survey

## Pause-Aware Depth Scheduling (PADS) for CPU-Only Edge Conversational Inference

**Purpose of this document:** a complete, thematically organized survey covering every research thread PADS touches, positioned explicitly against each. Six threads are covered: (A) LLM routing/cascading, (B) self-speculative early-exit decoding, (C) on-device/edge LLM serving, (D) quantization, (E) knowledge distillation for small/conversational models, (F) spoken dialogue, turn-taking, and predictive prefetching. A synthesis section (G) states exactly where PADS sits relative to all six.

---

## A. LLM Routing and Cascading

The idea of sending easy queries to a small model and hard queries to a large model is a mature, actively developed subfield as of 2024–2026, not an open problem.

- **RouteLLM** [A1] formulates routing as binary classification: predict whether a large model (e.g., GPT-4) would be preferred over a small one (e.g., Mixtral-8x7B) for a given query, trained on preference data from the Chatbot Arena leaderboard using a Bradley-Terry ranking approach.
- **MixLLM** [A2] extends this to a dynamic, contextual-bandit-based router that continually learns query-LLM assignments, balancing quality, cost, and latency, and explicitly critiques static classifier-only approaches (e.g., HybridLLM, RouterBench, FORC) for not adapting over time.
- **Lookahead Routing** [A3] argues that classifying purely on the input query (without seeing how a model would respond) is fundamentally limited for ambiguous or multi-step queries, and instead trains the router to predict the *latent representation* of each candidate model's likely response before committing to a route.
- A 2025–2026 survey [A4] categorizes the entire space — query-complexity inference, preference-similarity routing, domain-based routing, and cascading — and reports that query-level routing with a set of small LLMs (all under 9B parameters) can even outperform a single 70B model, evidence that routing itself is a well-validated, effective technique, not a research gap.
- **BEST-Route** [A5] adds a further refinement: choosing not just which model but how many samples to draw from it, based on difficulty and quality thresholds.

**Positioning:** HNIA's original "interaction layer routes to reasoning layer" framing is the literal shape of this literature. Any project reproducing a classifier-based small/large model router as its headline contribution would be indistinguishable from this existing body of work. PADS therefore does not build a router; the underlying "escalate or not" decision in PADS operates on **depth within one model**, not selection **between** models — a structurally different mechanism that avoids this crowded space entirely.

---

## B. Self-Speculative Early-Exit Decoding

This is the literature PADS's safe core is built on, and the correct fix for HNIA's original (technically invalid) assumption that two differently-sized models could exchange KV-cache state.

- **LayerSkip** [B1] (Elhoushi et al., ACL 2024) is the foundational method: train with layer dropout (low dropout at early layers, high at later layers) plus a shared early-exit loss so all layers can produce a usable output at a shared exit point; at inference, exit early to draft tokens, then continue through the remaining layers of the **same network** to verify — reusing the same KV-cache, with no auxiliary modules and up to ~2.16x speedup on Llama models.
- **CLaSp** [B2] introduces a plug-and-play, training-free layer-skipping strategy using dynamic programming to choose which layers to skip, achieving 1.3–1.7x speedups without retraining.
- **SWIFT** [B3] adaptively selects layers to skip per input, based on input-dependent layer sparsity (1.3–1.6x speedups across tasks).
- **ConfLayers** [B4] uses confidence-based layer selection; **KnapSpec** [B5] formulates draft-model/layer selection as a knapsack optimization problem.
- **QuantSpec** [B6] specifically studies self-speculative decoding under a **quantized** KV-cache (4-bit), directly relevant since PADS requires aggressive quantization to fit 16GB RAM — QuantSpec reports acceptance rates above 90% and up to 2.5x speedup even under quantization, though evaluated on GPU.
- The original two-model speculative decoding paper [B7] (Leviathan, Kalman, Matias, ICML 2023) remains the conceptual ancestor of the whole family and is useful for framing but is not the mechanism PADS uses (two-model KV-cache incompatibility is exactly the flaw self-speculative/early-exit methods avoid).

**Positioning:** Every one of these papers is evaluated on GPU-class hardware (A100/H100 or similar). **None reviewed characterizes early-exit self-speculative decoding on CPU-only, memory-bandwidth-bound consumer hardware** (e.g., a business laptop with no discrete GPU). This is the first identified gap PADS's safe core fills.

---

## C. On-Device / Edge LLM Serving

Establishes that edge/CPU-constrained LLM serving is an active, legitimate, and increasingly well-populated research area — important both as supporting context and as a caution against re-treading already-covered ground.

- **Prima.cpp** [C1] runs 30–70B models on heterogeneous, low-resource home clusters via pipelined-ring parallelism and a memory-pressure-aware scheduler that explicitly yields RAM to other foreground applications (e.g., not crashing a phone's browser while an LLM runs) — the closest existing precedent to PADS's "shared, single-user laptop" framing, though it addresses *not starving other apps*, not the assistant's own latency-hiding behavior.
- **"Challenging GPU Dominance"** [C2] directly probes whether CPUs can outperform GPUs for on-device inference, and finds thread scaling plateaus at 4–5 threads under memory-bandwidth/contention limits, with Q4 quantization offering a clear throughput benefit — directly informing PADS's Go/No-Go Test #1.
- **EnerInfer** [C3] focuses on energy-aware on-device serving, noting most commercial on-device systems favor NPUs over CPU/GPU specifically because of energy efficiency and to avoid interfering with foreground rendering tasks — relevant methodological grounding for PADS's energy-measurement plan, even though the Latitude 5490 has no NPU.
- **FlexInfer** and related memory-aware offloading systems [C4] use asynchronous prefetching and dynamic tensor placement to run models larger than available RAM — a complementary technique PADS could adopt if the RAM-budget Go/No-Go test fails.
- **Lever** [C5] applies speculative decoding specifically to reduce flash-resident "target model" invocations on smartphones, in a similar spirit to PADS but targeting storage-hierarchy cost rather than pause-time latency hiding.
- A broad survey on collaborative on-device/cloud model learning [C6] frames the general design space (device does cheap work, cloud/large model does expensive work) that HNIA's original vision document sat within — useful for related-work framing of what HNIA/PADS is and is not attempting.

**Positioning:** This confirms the CPU/edge angle is real and current, but also crowded enough that "we deployed an LLM on a laptop" alone is not novel. PADS's contribution must be the specific mechanism (early-exit + pause-time triggering), evaluated on this class of hardware, not the mere fact of edge deployment.

---

## D. Quantization

Necessary supporting technique — PADS requires aggressive quantization to fit models within 16GB RAM, and quantization interacts with the safe core's acceptance-rate risk (Report §5.2).

- **AWQ** [D1] (Lin et al., MLSys 2024) — activation-aware weight quantization, a leading post-training method for on-device compression.
- **LLM-QAT** [D2] (Liu et al., ACL Findings 2024) — data-free quantization-aware training, relevant if post-training quantization proves insufficient for acceptable early-exit acceptance rates.
- **ZeroQAT** [D3] — zeroth-order optimization-based QAT, addressing the prohibitive backpropagation memory cost of standard QAT, relevant given the project's limited training compute budget.
- Multiple 2025–2026 surveys [D4, D5] catalog the PTQ-vs-QAT trade-off space (GPTQ, SmoothQuant, SpinQuant, and 1.58-bit "BitNet"-style extreme quantization), useful as a reference table rather than a technique to individually re-implement.

**Positioning:** Quantization is infrastructure PADS depends on, not a novelty claim in itself — the project should select an existing method (AWQ or standard llama.cpp GGUF quantization) rather than developing a new one, and spend its novelty budget on the depth-scheduling mechanism.

---

## E. Knowledge Distillation for Small / Conversational Models

Relevant if the safe-core reasoning model needs further compression beyond what a released LayerSkip checkpoint provides, and for grounding the "small model does conversational work" half of the original HNIA vision honestly.

- A comprehensive 2025 survey on collaborating small and large language models [E1] and a dedicated survey on knowledge distillation for LLMs [E2] catalog black-box distillation (data augmentation from a teacher), white-box distillation (logit/hidden-state matching, e.g., MiniLLM), and reasoning-specific distillation (chain-of-thought distillation, multi-teacher distillation for smaller LLMs).
- **CoDi** [E3] specifically targets distilling *conversational* grounded-reasoning ability into small models via synthesized multi-turn dialogue generation, directly relevant if a fully custom conversational small model is ever pursued (though the project's SKILL explicitly discourages this — start from released checkpoints instead).
- Work on distilling end-to-end voice assistants without instruction-training data [E4] is a useful reference if the project extends toward speech-native interaction in a later phase.

**Positioning:** Distillation is a fallback tool, not the headline contribution, and per the project's own mitigations (Report §6), the plan explicitly avoids from-scratch distillation data collection in favor of released checkpoints and existing labeled corpora.

---

## F. Spoken Dialogue, Turn-Taking, and Predictive Prefetching

The second half of the PADS fusion — establishing what "hiding latency in a pause" already means in the literature, and where the true fusion gap is.

- **Moshi** [F1] (Défossez et al., Kyutai, 2024) achieves real-time full-duplex spoken dialogue (~160–200ms latency) via a 7B text backbone (Helium) and a neural audio codec (Mimi) modeling user/system audio as parallel streams, removing explicit turn-taking altogether — but requires GPU-class hardware and a purpose-built codec, and is explicitly the ceiling PADS does not attempt to reach.
- **Personalized Predictive ASR** [F2] (Google, 2023) is the closest direct precedent for "using the pause productively": a secondary, lower-confidence endpoint threshold triggers speculative downstream processing before the final end-of-turn is confirmed, hiding part of the downstream pipeline's latency if the preliminary transcript is later confirmed.
- **Voice Activity Projection (VAP)** and its real-time CPU-capable implementations [F3], plus multimodal extensions incorporating gaze/pose, provide the turn-taking prediction signal PADS needs, already shown to run continuously on CPU.
- Krisp's lightweight (~6M parameter) audio-only turn-taking model [F4] is a concrete, practical reference architecture for a CPU-cheap turn-taking predictor.
- Google's end-to-end turn-taking predictor for conversational speech [F5] jointly optimizes ASR and end-of-turn detection, reporting over 97% recall / 85% precision at only 100ms added latency — evidence this class of model is both accurate and cheap enough for PADS's use.

**Positioning:** Predictive prefetching across the pause boundary is known (F2); CPU-capable turn-taking prediction is known (F3–F5); full-duplex dialogue is known but GPU-bound (F1). **No source reviewed combines predictive pause-time triggering with early-exit model-depth extension** — this is the second identified gap, and together with the CPU/edge characterization gap from Section B, constitutes PADS's complete novelty claim.

---

## G. Synthesis: Where PADS Sits

| Thread | Maturity | PADS's relationship to it |
|---|---|---|
| A. Routing/cascading | Mature, crowded, actively developed | Explicitly avoided as the core mechanism — cited as what NOT to rebuild |
| B. Self-speculative early exit | Mature on GPU, proven mechanism | **Foundation** — PADS's safe core reproduces and characterizes this on CPU/edge hardware, a gap in this literature |
| C. On-device/edge serving | Active, moderately crowded | Supporting context; confirms CPU/edge is a legitimate niche without claiming this alone is novel |
| D. Quantization | Mature, standard tooling exists | Infrastructure dependency, not a novelty claim |
| E. Distillation | Mature, large literature | Fallback tool if needed; explicitly not the headline contribution |
| F. Turn-taking/predictive prefetch | Active, partially mature | **Foundation** — the pause-time triggering signal source; PADS fuses this with B for the stretch layer |

**PADS's stated contribution, precisely bounded by this survey:** (1) the first systematic characterization (among sources reviewed) of self-speculative early-exit decoding on CPU-only, memory-bandwidth-bound consumer hardware, with a dialogue-act-driven exit policy compared against the standard token-confidence exit; and (2), as a stretch goal, the first attempt (among sources reviewed) to trigger early-exit depth extension speculatively *during* a predicted conversational pause, rather than only in response to a completed prompt.

---

## References (grouped by section)

**A.** [A1] Ong et al., arXiv:2406.18665, 2024. [A2] "MixLLM," arXiv:2502.18482, 2025. [A3] "Lookahead Routing," arXiv:2510.19506, 2025. [A4] "Doing More with Less" survey, arXiv:2502.00409, 2025/2026. [A5] "BEST-Route," arXiv:2506.22716, 2025.

**B.** [B1] Elhoushi et al., "LayerSkip," ACL 2024, arXiv:2404.16710. [B2–B5] "Component-Aware Self-Speculative Decoding in Hybrid Language Models" (surveys CLaSp/SWIFT/ConfLayers/KnapSpec), arXiv:2605.01106, 2026. [B6] "QuantSpec," arXiv:2502.10424, 2025. [B7] Leviathan, Kalman, Matias, ICML 2023.

**C.** [C1] "Prima.cpp," arXiv:2504.08791, 2025. [C2] "Challenging GPU Dominance," arXiv:2505.06461, 2025. [C3] "EnerInfer," arXiv:2606.23001, 2026. [C4] On-device LLM inference survey (FlexInfer, DiSCo), emergentmind.com, 2025. [C5] "Lever: Speculative LLM Inference on Smartphones," arXiv:2605.16786, 2026. [C6] "Collaborative Learning of On-Device Small Model and Cloud-Based Large Model," arXiv:2504.15300, 2025.

**D.** [D1] Lin et al., "AWQ," MLSys 2024. [D2] Liu et al., "LLM-QAT," ACL Findings 2024. [D3] "ZeroQAT," OpenReview, 2025. [D4] "Survey of QAT Applications," 2025. [D5] "A Survey On Neural Network Quantization," 2025.

**E.** [E1] "A Survey on Collaborating Small and Large Language Models," arXiv:2510.13890, 2025. [E2] "Survey on Knowledge Distillation for Large Language Models," arXiv:2407.01885, 2024. [E3] "CoDi: Conversational Distillation for Grounded Question Answering," arXiv:2408.11219, 2024. [E4] "Distilling an End-to-End Voice Assistant Without Instruction Training Data," ACL 2025.

**F.** [F1] Défossez et al., "Moshi," arXiv:2410.00037, 2024. [F2] "Personalized Predictive ASR for Latency Reduction in Voice Assistants," arXiv:2305.13794, 2023. [F3] "RESPOND," arXiv:2603.21682, 2026. [F4] Krisp, "Audio-only Turn-Taking Model for Voice AI Agents," 2025. [F5] Chang et al. (Google), "Turn-Taking Prediction for Natural Conversational Speech," arXiv:2208.13321, 2022.

*(Convert to strict IEEE numbered format with full page/volume details once the exact cited paper versions are locked for the final manuscript — several 2026-dated arXiv IDs above should be re-checked for a published venue version before final submission, as some may have moved from preprint to conference/journal publication by then.)*

---

## H. Critical Update — Deep Research Pass (added after venue correction)

Three findings from a subsequent, deeper literature pass are load-bearing enough to change the plan, not just decorate it. All three are folded into the IEEE-formatted manuscript (`paper/PADS_manuscript.tex`) and the Go/No-Go test suite.

### H.1 Venue correction: ICSE is not a fit
ICSE's own scope language states that papers "which only peripherally concern software engineering" are out of scope — a CPU-inference-latency systems paper does not fit. Verified against the ICSE 2027 Research Track call. **Corrected target tier: MLSys, USENIX ATC/OSDI, EuroSys, IEEE EdgeSys/SEC, IEEE Transactions on Mobile Computing / IoT Journal, with NeurIPS-caliber workshops (Efficient ML, ES-FoMo) and the CVPR EDGE workshop as fast on-ramps.** MLSys 2026's own call for papers explicitly covers "systems for machine learning," including edge/on-device inference — confirmed by direct search.

### H.2 Early-exit adaptability is *decreasing* in modern LLMs — a load-bearing caveat
Wei et al., "The Diminishing Returns of Early-Exit Decoding in Modern LLMs" (arXiv:2603.23701, 2026) systematically measures early-exit adaptability (a new metric: logit-similarity between intermediate and final layers) across Llama2→Llama4, Qwen2/3, GPT-OSS, and Mamba families. Key results directly relevant to PADS:

- Early-exit suitability **decreases** across model generations as pretraining recipes and instruction/alignment tuning concentrate decision-relevant computation in later layers (post-training tuning measurably *reduces* a model's early-exit adaptability score, EAS).
- Larger dense transformers (>20B parameters) retain the most exploitable redundancy; MoE and SSM (Mamba) architectures are markedly less suitable.
- Critically: **models specifically fine-tuned for early exit recover much of the lost adaptability** — Llama3-8B (not tuned) scores EAS=0.46; LayerSkip-Llama3-8B (early-exit-tuned) scores EAS=0.54, comparable to Llama2-7B (0.52). This *validates* the project's plan to continued-fine-tune with LayerSkip's recipe rather than rely on an off-the-shelf instruction-tuned checkpoint — but it also means conversational alignment tuning and early-exit tuning may pull in opposite directions, which needs its own ablation.

**Action taken:** Go/No-Go Test 3 (off-the-shelf acceptance rate) is strengthened to explicitly measure EAS (via the logit-similarity metric this paper defines) for candidate base *and* fine-tuned checkpoints before committing to one, rather than assuming any small instruction-tuned model will behave like Llama2-class models from the original LayerSkip paper.

### H.3 Two prior systems sit closer to PADS than initially found — both require precise differentiation
A second-pass search surfaced two systems close enough that a reviewer will directly ask "how is this different?" Both are now cited and differentiated explicitly in the manuscript's Related Work section.

**Venkatesha, Kundu, and Panda, "Fast and Cost-effective Speculative Edge-Cloud Decoding with Early Exits" (arXiv:2505.21594, 2025; Yale/Intel Labs).** A small draft model runs on an edge device (Jetson Nano/Orin), a large target model with early-exit adapters runs on a cloud A100 server; partial, early-verified tokens let the edge device *preemptively draft* the next batch before final verification completes — exploiting idle client time during the network round-trip. Reports up to 35% latency reduction over cloud autoregressive decoding, plus 11% further from preemptive drafting.

*Why it's not PADS:* it is a **two-model** system requiring a persistent cloud connection, not a single self-speculative model running fully offline. The idle time it exploits is **network/verification round-trip time on an already-complete prompt**, not the human pause before a turn has finished. All reported speedups are measured with an A100 in the loop, not CPU-only hardware. This is the closest *mechanism*-level analog found; PADS differs on model count, network dependency, and — most importantly — *what idle time is being exploited*.

**Ok, Yoo, and Lee, "Speculative End-Turn Detector for Efficient Speech Chatbot Assistant" (arXiv:2503.23439, 2025/2026; POSTECH/KAIST).** A ~200K-parameter on-device GRU continuously flags speech vs. silence in real time; only when it detects silence does a much larger server-side Wav2Vec2 model perform the harder classification of pause-vs-gap (i.e., hesitation vs. real end-of-turn). Explicitly named after speculative decoding for its cheap-then-expensive cascade structure. Also releases OpenETD, the first public end-turn-detection dataset (120K+ synthetic + real samples), directly useful as a training/eval resource for PADS's turn-taking component.

*Why it's not PADS:* it is the closest work **by name**, but its contribution stops at deciding *whether* to invoke the downstream LLM at all — it never touches model depth or the LLM's own computation, and its heavy stage still requires a server round-trip. PADS uses the same *class* of signal (lightweight, continuous, on-device) but to decide *how deep* into an already-invoked, fully local model to compute, before the turn-detection decision is even finalized.

**Net effect:** no source found (across two search passes and three full-paper reads) combines turn-level predictive triggering with model-*depth* extension within a single self-speculative model, evaluated on CPU-only hardware. The compound gap holds, but the boundary against these two systems must be stated precisely and early in any submission, since both are plausible reviewer "isn't this already done?" candidates.
