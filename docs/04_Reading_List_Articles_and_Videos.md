# Reading & Viewing List — HNIA / PADS

Organized by topic, roughly in the order you'll need them. Papers marked ★ are the core foundation for the safe-core and stretch-layer contributions; read those first.

---

## A. Self-speculative / early-exit decoding (core foundation) ★

1. ★ Elhoushi et al., **"LayerSkip: Enabling Early Exit Inference and Self-Speculative Decoding,"** ACL 2024. arXiv:2404.16710 — https://arxiv.org/abs/2404.16710 — read this first, in full. Also see the official code: https://github.com/facebookresearch/LayerSkip
2. **"Component-Aware Self-Speculative Decoding in Hybrid Language Models"** (surveys CLaSp, SWIFT, ConfLayers, KnapSpec), arXiv:2605.01106 — good single source to understand the family of early-exit variants beyond LayerSkip.
3. **"QuantSpec: Self-Speculative Decoding with Hierarchical Quantized KV Cache,"** arXiv:2502.10424 — relevant because you'll be quantizing anyway; shows how self-speculative decoding interacts with quantized KV caches.
4. Leviathan, Kalman, and Matias, **"Fast Inference from Transformers via Speculative Decoding,"** ICML 2023 — the original two-model speculative decoding paper; read for historical grounding even though your mechanism is self-speculative, not two-model.
5. Google Research, **"Looking Back at Speculative Decoding"** — https://research.google/blog/looking-back-at-speculative-decoding/ — accessible, well-illustrated overview.

## B. LLM routing / cascading (read to understand what NOT to build) 

6. Ong et al., **"RouteLLM: Learning to Route LLMs with Preference Data,"** arXiv:2406.18665.
7. **"MixLLM: Dynamic Routing in Mixed Large Language Models,"** arXiv:2502.18482.
8. **"Doing More with Less: A Survey on Routing Strategies for Resource Optimisation in LLM-Based Systems,"** arXiv:2502.00409 — the single best overview of how crowded this space is; use this to write your related-work section precisely.

## C. On-device / edge LLM serving ★

9. ★ **"Prima.cpp: Fast 30–70B LLM Inference on Heterogeneous and Low-Resource Home Clusters,"** arXiv:2504.08791 — closest existing work to your hardware constraints; read the memory-pressure section carefully.
10. **"Challenging GPU Dominance: When CPUs Outperform for On-Device LLM Inference,"** arXiv:2505.06461 — directly relevant to your Go/No-Go test #1 (bandwidth-vs-compute).
11. **"EnerInfer: Energy-Aware On-Device LLM Inference,"** arXiv:2606.23001 — for your energy-measurement methodology.
12. **"Collaborative Learning of On-Device Small Model and Cloud-Based Large Model: Advances and Future Directions,"** arXiv:2504.15300 — good survey framing for positioning against the original HNIA vision.
13. J. Lin et al., **"AWQ: Activation-Aware Weight Quantization for On-Device LLM Compression and Acceleration,"** MLSys 2024 — practical quantization method you'll likely use or compare against.
14. Z. Liu et al., **"LLM-QAT: Data-Free Quantization Aware Training for Large Language Models,"** ACL Findings 2024.

## D. Spoken dialogue, turn-taking, and predictive prefetching (second half of the fusion) ★

15. ★ Défossez et al., **"Moshi: A Speech-Text Foundation Model for Real-Time Dialogue,"** arXiv:2410.00037 — read for the full-duplex architecture and its GPU dependency (this is what you're NOT reproducing, but must cite and position against).
16. ★ **"Personalized Predictive ASR for Latency Reduction in Voice Assistants,"** arXiv:2305.13794 — the closest existing precedent for "start computing before the turn actually ends."
17. **"RESPOND: Responsive Engagement Strategy for Predictive Orchestration and Dialogue,"** arXiv:2603.21682 — covers Voice Activity Projection (VAP) and CPU-capable predictive turn-taking models.
18. Krisp, **"Audio-only, 6M-weight Turn-Taking Model for Voice AI Agents"** — https://krisp.ai/blog/turn-taking-for-voice-ai/ — practical, lightweight, CPU-friendly reference implementation to study.
19. Chang et al. (Google), **"Turn-Taking Prediction for Natural Conversational Speech,"** arXiv:2208.13321.

## E. Practical / tooling guides (for implementation, not citation)

20. **llama.cpp Tutorial: Run a Local LLM in 12 Steps** — https://tech-insider.org/llama-cpp-tutorial-2026/ — practical GGUF conversion/quantization walkthrough.
21. **"GGUF in Practice: From Model to Production"** (Parts 1–2), Medium — https://medium.com/@michael.hannecke/gguf-in-practice-from-model-to-production-part-2-27c7eed23daa
22. **"Running LLMs on Raspberry Pi and Edge Devices"** — https://www.sitepoint.com/llms-raspberry-pi-edge/ — useful even though your primary device is the Latitude 5490; same toolchain (llama.cpp/GGUF).
23. **vLLM Blog, "How Speculative Decoding Boosts vLLM Performance by up to 2.8x"** — https://blog.vllm.ai/2024/10/17/spec-decode.html — good production-system perspective, though vLLM itself is GPU-oriented.

---

## Videos

24. **"Lecture 22: Hacker's Guide to Speculative Decoding in vLLM"** — https://www.youtube.com/watch?v=9wNAgpX6z_4 — solid technical walkthrough, watch after reading item 4.
25. **"Speculative Decoding: When Two LLMs are Faster than One"** — https://www.youtube.com/watch?v=S-8yr_RibJ4 — good visual intuition for beginners on the team.
26. **"Speculative Decoding Explained"** (Adaptive ML) — https://www.youtube.com/watch?v=p23SblAIoXc — has an accompanying written version at adaptive-ml.com, useful for note-taking.
27. **"Speculative Decoding: Make Your LLM Inference 2x-3x Faster"** — https://www.youtube.com/watch?v=etz4VCx02rI

*(Search directly on YouTube for "LayerSkip early exit ACL 2024" and "llama.cpp Raspberry Pi GGUF setup" for the most current walkthroughs — these ecosystems update frequently enough that a live search close to when you actually start implementation will surface more current tutorials than a fixed list can.)*

---

## Suggested reading order for a new team member

1. Item 5 (Google's speculative decoding blog) — intuition, 15 minutes.
2. Video 25 — visual reinforcement.
3. Item 1 (LayerSkip paper, full read) — the actual mechanism you're building on.
4. Item 8 (routing survey) — understand what's already solved, so you don't rebuild it.
5. Items 15–17 (Moshi, predictive ASR, RESPOND) — the second half of the fusion.
6. Items 9–10 (prima.cpp, CPU-vs-GPU study) — why your hardware constraint is a real research niche.
7. Items 20–22 — start building.
