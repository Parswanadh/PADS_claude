# HNIA / PADS — Build & Research Repository

Pause-Aware Depth Scheduling: CPU-only edge conversational inference via self-speculative early exit, evaluated toward an IEEE Transactions-caliber submission.

**Read `/docs/03_SKILL.md` first if you are an agent or new contributor** — it states what NOT to build and the mandatory build order.

**Target venues** (corrected after direct verification of scope — see `docs/06_Literature_Survey.md` §H.1): MLSys, USENIX ATC/OSDI, EuroSys, IEEE EdgeSys/SEC, IEEE Transactions on Mobile Computing or IoT Journal, with NeurIPS-caliber workshops (Efficient ML, ES-FoMo) and the CVPR EDGE workshop as fast on-ramps. **ICSE is explicitly not a fit** — verified against its own call for papers, which excludes work that only peripherally concerns software engineering.

**Manuscript:** `paper/PADS_manuscript.tex` — a compiling, verified IEEE Transactions-format (`IEEEtran`, journal mode) draft. Compiled cleanly to a 5-page PDF with zero LaTeX warnings/errors (3-pass pdflatex, all citations and cross-references resolved) in this repository's own verification pass. It reports only executed/verified results (Section V) and treats everything else as a pre-registered, not-yet-run evaluation plan — do not backfill placeholder numbers into it; run the Go/No-Go suite and real benchmarks first.

## Status of this repository

This scaffold was built inside a sandboxed development container **without** the target Dell Latitude 5490 hardware, without a discrete GPU, and without downloading multi-gigabyte model weights (blocked by the sandbox's network allowlist and impractical for a scaffold). Everything that is hardware-agnostic has been written, executed, and verified to run correctly in this container. Everything that requires the actual target machine, real model weights, or real audio hardware is clearly marked `REQUIRES TARGET HARDWARE` with exact instructions for what to run once the repository is copied to the Latitude 5490.

## Directory layout

```
setup/                  environment setup (llama.cpp build, Python deps)
experiments/go_no_go/   the 7 falsification tests — run these FIRST, on real hardware
experiments/results/    raw logs + verification results (llama.cpp build log, unit test logs)
src/trigger_policy/     the conservative asymmetric trigger logic (hardware-agnostic, tested here)
src/dialogue_act/       dialogue-act classifier training pipeline (tested here on synthetic data)
src/turn_taking/        turn-taking predictor integration point (requires real audio corpus)
src/eval/               benchmark harness + metrics logging (hardware-agnostic, tested here)
docs/                   Report, PRD, SKILL, Reading List, PPT content, and Literature Survey
paper/                  IEEE Transactions-format manuscript (.tex, verified-compiling .pdf)
```

## What has been verified to actually run in this sandbox

- `src/trigger_policy/policy.py` + its test suite — **PASSED**, see `experiments/results/trigger_policy_test_log.txt`
- `src/dialogue_act/train_classifier.py` — trained end-to-end on a small synthetic dialogue-act dataset — **PASSED**, see `experiments/results/dialogue_act_training_log.txt`
- `src/eval/benchmark_harness.py` — runs its self-test in mock-timing mode — **PASSED**, see `experiments/results/benchmark_harness_selftest_log.txt`
- `experiments/go_no_go/test5_ram_budget.py` — runs and reports real container RAM figures (not the Latitude 5490's, but the script itself is verified working)
- `setup/setup_llama_cpp.sh` — actually cloned and built (CMake configure passed cleanly; compilation reached ~60% with zero errors before a single-core sandbox timeout, not a build failure). Found and fixed a real issue in the process: the default build pulls in an unnecessary npm-based web UI target, now disabled via `-DLLAMA_BUILD_UI=OFF`. Full log: `experiments/results/llamacpp_build_verification_log.md`
- `paper/PADS_manuscript.tex` — compiled end-to-end with `pdflatex` (3 passes) after installing `texlive-publishers` for `IEEEtran.cls`. Zero warnings, zero errors, all citations/cross-references resolved, verified page-by-page by rendering to images.

## What still requires the real target hardware (cannot be done in this sandbox)

- Building/running llama.cpp against a real GGUF model and measuring true tokens/sec, TTFT, thread-scaling behavior (Go/No-Go test #1)
- Real pause-duration statistics from Switchboard/CallHome vs. this exact CPU's decode-step timing (Go/No-Go test #2)
- Acceptance-rate measurement of a real LayerSkip checkpoint (Go/No-Go test #3)
- Thermal throttling behavior over a 30-minute sustained run (Go/No-Go test #4)
- RAPL/turbostat/powertop or USB power-meter energy readings (Go/No-Go test #6)
- Real turn-taking predictor integration against live or recorded audio

## First commands to run once this is on the Latitude 5490

```bash
bash setup/setup_llama_cpp.sh
pip install -r setup/requirements.txt
bash experiments/go_no_go/test1_bandwidth_vs_compute.sh   # after placing a GGUF model per its header comment
python experiments/go_no_go/test5_ram_budget.py
bash experiments/go_no_go/test4_thermal_stability.sh
bash experiments/go_no_go/test6_energy_tooling.sh
```

Do not proceed to building the full pipeline until all seven Go/No-Go tests have a logged result in `experiments/go_no_go_results.md` (template provided).
