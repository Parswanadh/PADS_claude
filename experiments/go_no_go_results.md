# Go/No-Go Test Results Log

Fill in as each test is run on the target hardware. This file is a required project artifact — do not proceed to full pipeline implementation (Build Order §3 in the SKILL) until all seven have an entry.

| # | Test | Date run | Result (PASS / FAIL / PIVOTED) | Key numbers | Decision / next action |
|---|---|---|---|---|---|
| 1 | Bandwidth-vs-compute | 2026-08-07 | **FAILED (bandwidth-bound) — kill signal fired, as pre-registered** | Real run against `facebook/layerskip-llama3.2-1B` (Q4_K_M) on this dev machine, `-t 1..8`, `-n 128`: **1**:16.7 t/s, **2**:30.2, **3**:36.5, **4**:43.5, **5**:47.2, **6**:48.7, **7**:49.3, **8**:49.1 tok/s. Near-linear scaling 1→4 threads, then a clear flatline from 5 threads onward (47.2→48.7→49.3→49.1, essentially plateaued, within noise). This is exactly the test's own kill signal ("flatlines past 4-5 threads → bandwidth-bound"). Notably this is already a **1B model** (smaller than the report's fallback suggestion of shrinking to 3B) and it's still clearly bandwidth-bound — a robust confirmation, not a marginal one. Fixed two real bugs in `test1_bandwidth_vs_compute.sh` before this could run at all: (1) it hung indefinitely — this llama.cpp build auto-enables interactive conversation mode for chat-template models, needed `-st` + stdin-from-`/dev/null` (see `llamacpp_inference_smoke_test.md`); (2) its output-parsing regex targeted an older CLI format ("eval time ... tokens per second") that doesn't exist in this build (actual format: `[ Prompt: X t/s \| Generation: Y t/s ]`) — every run would have silently logged "NA". Both fixes committed to the script itself, not just worked around ad hoc. | **Per `docs/01_HNIA_PADS_Detailed_Report.md` §6's pre-committed mitigation**: "Reframe as a legitimate characterization result... shrink the reasoning model to test whether a smaller model shifts the regime back toward compute-bound." Already done — 1B is smaller than the suggested 3B fallback, still bandwidth-bound. This is the expected, historically-anticipated finding that motivates PADS's entire premise (if CPU inference were compute-bound, there'd be nothing for pause-time extra compute to usefully exploit) — log as a legitimate research result, not a project failure, and proceed. Real numbers, dev machine (Alienware m16 R2), not target hardware (Dell Latitude 5490) — re-run there before any paper-reportable claim. |
| 2 | Pause-duration feasibility | 2026-08-08 | **FAILED — kill signal fired, but by a razor-thin, likely-artifactual margin** (median pause 260.0ms vs median step 263.2ms; 3.2ms / ~1% apart) | **Both halves now real for the first time.** Decode-step timing: unchanged from 2026-08-07 (n=147 real steps via `self_speculation_generator.py` instrumentation, median 263.2ms — see prior entry, PyTorch reference implementation, not the faster quantized llama.cpp path). **Corpus (newly resolved via a verified free alternative, not LDC):** Switchboard/CallHome remain LDC-gated and unresolved, but the **AMI Meeting Corpus** manual annotations (CC BY 4.0, no LDC gating, no registration wall — verified directly: HTTP 200 unauthenticated download, https://groups.inf.ed.ac.uk/ami/download/) provide real word-level timestamps per speaker per meeting. Wrote `experiments/go_no_go/test2_extract_ami_pause_durations.py`: merges all speakers' word timings chronologically per meeting, records the gap at every real speaker transition (Heldner & Edlund's "gap" definition). Raw extraction: 171 meetings, 64,415 real between-speaker gaps, median 260.0ms, mean 610.6ms (heavily right-skewed by a long tail to 137.6s — almost certainly meeting-structural breaks, not turn-taking gaps). Filtered to exclude likely "lapses" (>10s, only 0.38% of data, matching the pause/gap/lapse distinction in Sacks et al. and the already-cited Heldner & Edlund): n=64,173, median unchanged at 260.0ms, mean 544.3ms, p25=110ms, p75=610ms — closely matching the general literature range already cited in the manuscript (stivers2009universals, heldner2010pauses), a good sanity check that the extraction is sound. Ran the actual `test2_pause_duration_check.py --pauses <AMI filtered> --steps <real decode-step data>` for the first time: **49.0% of real pauses are long enough to fit one real depth-extension step; the kill signal (median pause < median step) fires by 3.2ms.** | **Two important caveats, not excuses, real methodological facts:** (1) AMI is 4-5 person, in-person, task-oriented business meetings, not Switchboard/CallHome's dyadic telephone conversation register — a genuinely different, freely-verified alternative corpus, not a substitute claimed to be equivalent. (2) The step-timing side used the slower PyTorch reference implementation, not the quantized llama.cpp pipeline Test 1's 49 tok/s ceiling suggests is achievable — a real deployment's depth-extension step would very plausibly be faster, which could flip this 3.2ms deficit to a surplus. Given the margin is within likely measurement/implementation noise, this is honestly logged as FAILED per the script's own strict logic (not softened), but flagged prominently as near-parity, not a clear failure. Per the test's pre-committed action for this outcome: redesign timing granularity rather than just re-tune thresholds. Two concrete next steps identified, not yet done: (a) re-measure decode-step time via the quantized llama.cpp pipeline instead of the PyTorch reference implementation — the single most likely thing to resolve this near-tie; (b) since 49% of real pauses already clear the bar, "exploit only the longer pauses" (the test's own suggested fallback) is already a viable, evidenced fallback design, not just a hypothetical one. All data/scripts preserved: `experiments/go_no_go/test2_extract_ami_pause_durations.py`, `experiments/results/test2_ami_pause_durations.json` (raw), `experiments/results/test2_ami_pause_durations_filtered.json` (lapse-excluded, used for the official comparison). |
| 3 | Off-the-shelf acceptance rate | 2026-08-07 | **PASSED** — mean acceptance rate 86.4%, well above "too low to matter" | Real run: `facebook/layerskip-llama3.2-1B` (unmodified, off-the-shelf), `--generation_strategy self_speculative --exit_layer 3` (the model-card-recommended exit layer for this specific 1B checkpoint, not the 7B example's layer 8) `--num_speculations 6 --no_sample` (greedy, matching the LayerSkip paper's own reported methodology). 8 samples, per-sample acceptance: 89.6%, 84.9%, 86.8%, 90.4%, 84.6%, 100%, 75.1%, 80.1% — **mean 86.4%**. Dataset: a small (n=8), hand-authored, clearly-synthetic conversational prompt set (`experiments/results/test3_conversational_prompts.jsonl`) — chosen deliberately over the script's default CNN/DM summarization per `docs/03_SKILL.md`'s own guidance to prefer conversational-style prompts, and also because it structurally routes around a real Python 3.14 incompatibility in the HF `datasets` library (see notes). **Caveat for interpretation**: this is a *base*, non-instruction-tuned model, and its generations on unstructured prompts were highly repetitive (e.g., looping the same sentence) — repetitive continuations are easier for a draft model to predict, so this 86.4% may be somewhat inflated relative to what a more coherent/instruction-tuned setup would show. Treat as a genuine, real, non-fabricated feasibility signal, not a final paper-reportable number (small n=8, synthetic prompts, dev hardware). | **Real bugs found and fixed to get here, not blindly retried**: (1) `torchrun` launch triggered a `transformers` 4.50.0 tensor-parallel/accelerator-sharding code path incompatible with CPU-only + `device_map="auto"`; fixed by making `device_map` conditional on device in `generate.py`. (2) `transformers` 4.50.0 now requires the caller to precompute rotary `position_embeddings` and pass them to each decoder layer explicitly (previously computed internally); added this in all 4 decoder-layer call sites across `forward`/`forward_early`/`forward_remainder` in `self_speculation/llama_model_utils.py`. (3) `LlamaDecoderLayer.forward()` now returns only `(hidden_states,)`, not `(hidden_states, past_key_values)` — the cache mutates in place via the passed `DynamicCache` object now; fixed the same 4 call sites. (4) A real Python 3.14 incompatibility in `dill`'s pickle internals (`_batch_setitems` signature) broke `datasets.load_dataset`'s cache-fingerprint hashing even at the latest dill release (0.4.1) — routed around it entirely via `--dataset custom_jsonl` (a pure-pandas load path with no `datasets`/dill involvement), which also happened to align with the project's own preference for conversational prompts. All fixes preserved as a git patch: `experiments/results/layerskip_python314_transformers450_compat.patch` (LayerSkip/ itself is gitignored as an external clone, so the patch is what's tracked). Also relaxed three old exact-pinned dependency versions with no Python 3.14 wheels (torch, pandas, sentencepiece) to get the environment installed at all. Not target hardware (Dell Latitude 5490) — dev machine numbers. |
| 4 | Thermal stability | 2026-08-07 (assessed, not run) | NOT STARTED — `lm-sensors` gap now resolved; still needs explicit go-ahead for the 30-min run | Script (`test4_thermal_stability.sh`) requires a GGUF model (currently only the ungated TinyLlama-1.1B stand-in exists, not the real LayerSkip checkpoint) and runs a **fixed 30-minute (1800s) sustained max-load inference loop**. Unlike Tests 1/3, this one *could* technically run today using the TinyLlama stand-in (thermal throttling is a hardware/BIOS property, not model-specific) — but that's a materially different risk category than anything run so far (81s compile, <30s inference smoke test): 30 minutes of sustained full CPU load, unattended, on a shared workstation with other real active processes (browser, editor, another agent session, Docker Desktop observed running). `lm-sensors` was installed alongside Test 6's fix (2026-08-07) — `sensors` now works, so a future run would capture real temperature data, not just frequency. | **Deliberately not run without the user's explicit go-ahead** for a 30-minute sustained-load window, given the shared-machine disruption profile — this is a duration/consent judgment call, not a technical blocker Claude Code should resolve unilaterally. Both technical prerequisites (a model to run and `lm-sensors` for temperature) are now satisfied (TinyLlama stand-in + lm-sensors installed); only the timing go-ahead remains. |
| 5 | RAM budget | 2026-08-08 | PARTIAL — real LLM-process RSS now measured; classifier/turn-taking components still don't exist to sum | Script verified working (2026-08-07, unchanged). **New real data (2026-08-08):** measured actual peak RSS of the real quantized-model inference process directly (`/usr/bin/time -v ./llama-cli -m layerskip-llama3.2-1b-Q4_K_M.gguf ...`, real checkpoint, 21 threads, 32 tokens): **Maximum resident set size = 4,758,740 KiB ≈ 4.54 GiB (~4.87 GB)**. Checked resources before and after — system recovered cleanly, no lasting memory pressure. Against the script's own budget arithmetic (16GB total − 3GB headroom = 13GB usable), this single-process real number leaves ~8.2GB of headroom for the dialogue-act classifier and turn-taking predictor once those are built. | This is real progress, not the full pipeline result — the classifier and turn-taking predictor don't exist yet (they're safe-core/stretch-layer work, per `docs/03_SKILL.md` build order), so there's nothing to sum them with yet. The LLM process is the dominant, now-measured component; the remaining gap is small components that are lightweight by design (SKILL.md explicitly requires the dialogue-act classifier to be "CPU-cheap enough to run alongside... the LLM inference process... without contending for the same cores/RAM"). Not target hardware (Alienware m16 R2, not Dell Latitude 5490) — re-run there before treating as final. |
| 6 | Energy tooling | 2026-08-07 (resolved) | **PASSED** — RAPL/turbostat/powertop all usable | User provided sudo credentials directly (used once, then `sudo -k` to clear the cache immediately after — not stored anywhere). Installed `lm-sensors` and `powertop` (`sudo apt-get install -y lm-sensors powertop`). All three methods produced plausible, non-zero, reproducible readings: **turbostat** (`sudo turbostat --interval 5 --num_iterations 3`) reported real per-core and package power across all 3 samples — PkgWatt 13.88–14.36W, PkgTmp 68–81°C, RAPL package limits (200W/28s and 125W/2.4ms) correctly detected. **powertop** (`sudo powertop --csv=experiments/results/test6_powertop.csv --time=10`) produced a real software-power-consumer breakdown (saved to the CSV, tracked in this repo). **RAPL sysfs direct read** (`sudo cat .../intel-rapl:0/energy_uj`) returned a real large monotonic counter (166874425766), confirming root-level RAPL access works once permission-gated. | This machine's energy tooling is usable for future benchmarking, contingent on sudo access being available at benchmark-run time (each session needs it re-granted; nothing persists across reboots/sessions since no persistent non-root capability was set up). Note for later: still not the Dell Latitude 5490 target hardware — these are dev-machine power figures, not reportable target-hardware energy numbers. |
| 7 | Literature scoop check | 2026-08-07 (first run) | PASSED (as of 2026-08-07) | No exact fusion of "conversational pause as trigger" + "single-model self-speculative depth extension" found across all 6 queries. One new partial-overlap system found (arXiv:2511.07397, two-model talker/reasoner — opposite mechanism) and added to `docs/06_Literature_Survey.md` §H.4. | Continue as planned. Re-run biweekly — see per-instance log below and in the test7 checklist. Next due ~2026-08-21. |

## Test 7 — per-instance scoop check log

### Scoop check — 2026-08-07
Queries run: all 6 (pause-aware early exit LLM; predictive prefetch layer skipping conversational; speculative decoding conversational pause; early exit self-speculative CPU edge inference; dialogue act driven speculative decoding; turn-taking layer skip LLM)
Findings:
- No exact match on any query for the specific fusion (conversational-pause-triggered, single-model, self-speculative depth extension).
- Partial overlap, already known and cited (`docs/06_Literature_Survey.md` §H.3): Venkatesha et al. arXiv:2505.21594 (two-model edge-cloud speculative decoding, exploits network round-trip idle time, not human pause) and Ok et al. arXiv:2503.23439 (Speculative End-Turn Detector — decides *whether* to invoke the LLM, never touches model depth). Both resurfaced by this scoop check, confirming they're still the closest prior work and nothing closer has since appeared.
- Partial overlap, newly found: arXiv:2511.07397 "Thinking While Speaking" — two-model talker/reasoner latency-hiding architecture for voice agents. Verified by fetching the actual abstract (not just trusting the search snippet) before logging. Added as `docs/06_Literature_Survey.md` §H.4 with explicit differentiation (two-model vs. PADS's single-model depth extension; hides the *agent's own* reasoning latency vs. PADS hiding latency inside the *human's* pre-turn-end pause).
- Also surfaced (weaker overlap, cite as general related work, not differentiation-critical): predictive weight-prefetching work that uses early-layer activations to predict and prefetch later-layer weights ahead of need — conceptually adjacent ("use available time productively, ahead of need") but not tied to conversational pause and about weight I/O, not compute-depth extension.
Decision: continue as-is. No reposition needed. Re-run at next biweekly interval (~2026-08-21).

- A "FAIL" here is a valid research result, not a project failure — see Detailed Report §5–6 for the pre-committed pivot for each.
- Do not skip a test because "it'll probably pass" — several of these (especially #1 and #2) exist specifically because the intuitive assumption may be wrong.

## Test 2 supplementary analysis — quantized-pipeline speedup estimate (2026-08-08)

Test 2's official result (FAILED, median pause 260.0ms vs. median step
263.2ms) used decode-step timing measured on the PyTorch/`transformers`
reference implementation. This note estimates — as a clearly-labeled
**rough proxy, not a real measurement** — what the depth-extension step
might take on the faster quantized `llama.cpp` pipeline, since no
self-speculative early-exit implementation exists in `llama.cpp` to
measure directly.

**Real data used:** this session measured PyTorch FP16 plain
autoregressive decoding on the same checkpoint/prompts at **13.89 tok/s**
(72.0ms/token) — a genuine, direct measurement (`--generation_strategy
autoregressive`). Test 1 (2026-08-07) measured `llama.cpp` Q4_K_M plain
decoding at **~49.2 tok/s** (mean of the 7–8 thread plateau, 49.3/49.1).

**Estimate:** speedup ratio ≈ 49.2 / 13.89 ≈ **3.54×**. Applied naively to
the measured 263.2ms median step time: 263.2 / 3.54 ≈ **~74ms estimated
quantized step time**. If this scaling held, the depth-extension step
would comfortably clear even the AMI corpus's 25th-percentile real pause
(110ms), decisively resolving the near-tie in favor of feasibility.

**Why this is a rough estimate, not a revised result — do not treat the
~74ms figure as a real number:** `forward_remainder()` verifies a *batch*
of `num_speculations=6` drafted tokens in one forward pass — computationally
closer to prompt/prefill processing than to sequential token-by-token
decoding. `llama.cpp`'s own prompt-processing throughput (seen informally
across this session's raw `llama-cli` runs, ~200–270 t/s) is meaningfully
higher than its generation throughput (~49–59 t/s) used for this ratio,
which this estimate does not account for — the true speedup for a batched
verification pass could differ from the plain-sequential-decoding ratio
in either direction. Treat ~74ms as a plausibility argument that the
near-tie is likely resolvable, not as Test 2's real answer. A genuine
resolution needs either a real `llama.cpp`-based self-speculative
implementation (a real engineering task) or a more careful proxy using
prompt-processing throughput specifically.

## Test 2 follow-up (b) — concrete "exploit only longer pauses" threshold analysis (2026-08-08)

Test 2's row above identified fallback (b) — "since 49% of real pauses
already clear the bar, exploit only the longer pauses" — as a viable but
not-yet-concretized fallback design. This is a real analysis, computed
directly from the two already-saved real datasets
(`test2_ami_pause_durations_filtered.json`, n=64,173 real AMI gaps, and
`test2_decode_step_times.json`, n=147 real PyTorch-reference
depth-extension steps) — no new measurement or execution, just arithmetic
over existing real numbers.

Idea: instead of triggering PADS's depth-extension on every pause (where
the median step barely loses to the median pause), only trigger when the
*observed-so-far* pause duration already exceeds some threshold `T`. This
trades coverage (fraction of real pauses long enough to use) against
safety margin (fraction of real decode steps that fit inside `T` without
overrunning the pause).

| Threshold T | Pause coverage (% of real AMI pauses ≥ T) | Step fits-within (% of real steps ≤ T) |
|---|---|---|
| 200ms | 58.1% | 4.8% |
| 250ms | 51.5% | 10.9% |
| 260ms (current median-vs-median comparison) | 49.2% | 40.8% |
| 263.2ms (measured step median) | 49.0% | 51.0% |
| 280ms | 47.1% | 81.6% |
| **300ms** | **45.0%** | **91.2%** |
| 350ms | 40.2% | 94.6% |
| 400ms | 36.2% | 94.6% |
| 450ms | 32.7% | 94.6% |
| 500ms | 30.1% | 94.6% |
| 600ms | 25.4% | 94.6% |

**Reading this table:** the raw median-vs-median comparison (T≈260ms) is
a razor-thin, roughly coin-flip safety margin — only ~41-51% of real
steps actually finish before the pause does at that threshold, which is
consistent with Test 2's official near-tie FAILED result. Moving the
trigger threshold up to **T=300ms** is a concrete, evidenced fallback
design point: it still captures **45% of all real AMI pauses** (barely
down from 49% at the naive threshold) while raising the safety margin to
**91.2%** of real steps fitting comfortably inside the pause — a much
more robust operating point than the coin-flip margin at the raw median.
Beyond ~T=350-400ms the step-fit rate plateaus at 94.6% (the slowest
~5.4% of measured steps are far outliers, max 1062.3ms — plausibly GC
pauses, cache misses, or other measurement noise in the PyTorch reference
implementation rather than representative depth-extension cost), so
there's no real further safety benefit past that point, only lost
coverage.

**Caveats (same as the parent Test 2 entry, do not treat as resolved
independent of them):** step-timing data is from the slower PyTorch
reference implementation (n=147), not the quantized `llama.cpp` pipeline;
pause data is from AMI (multi-party meetings), not Switchboard/CallHome
(dyadic calls). This table is a real, direct computation over existing
real data, not a new experiment — it does not change Test 2's official
FAILED status, it gives the previously-abstract fallback (b) a concrete,
evidence-based starting threshold (**T≈300ms**) for future work once a
turn-taking predictor exists to supply pause-so-far duration as a live
signal.
