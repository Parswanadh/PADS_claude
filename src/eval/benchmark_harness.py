"""
Benchmark harness for comparing configurations required by the PRD (Sec 15):
plain decoding, standard speculative decoding, plain cascading, LayerSkip's
own config, safe-core (dialogue-act exit), and PADS (pause-time trigger).

REQUIRES TARGET HARDWARE for real numbers (calls out to llama.cpp / a real
inference process). This file also includes a --selftest mode using mock
timing, so the harness's aggregation/logging/reporting logic itself is
verified correct in this sandbox before it's pointed at real hardware.

Non-negotiable per SKILL Sec 5:
  - fixed warm-up + discard-first-runs (thermal protocol, Go/No-Go test 4)
  - multiple seeds/runs, report mean +/- CI, never a single number
  - raw logs stored, not just aggregates
"""
import argparse
import random
import time

from metrics import RunMetrics, aggregate, save_runs_jsonl


WARMUP_RUNS = 2          # discarded, per Go/No-Go test 4 findings
MEASURED_RUNS = 8        # minimum for a non-trivial CI


def run_once_REAL(config_name: str, model_path: str) -> RunMetrics:
    """
    REQUIRES TARGET HARDWARE. Placeholder showing the intended integration
    point: shell out to llama.cpp (or the PADS pipeline), parse its timing
    output, and read RAM via psutil / the Go/No-Go test 5 helper, and energy
    via the Go/No-Go test 6 tooling (or its USB-power-meter fallback).
    """
    raise NotImplementedError(
        "Wire this up to the actual llama.cpp / PADS pipeline invocation on "
        "the Latitude 5490. Left unimplemented deliberately -- do not fill "
        "this in with fabricated numbers; measure them."
    )


def run_once_MOCK(config_name: str, base_ttft_ms: float, base_tps: float) -> RunMetrics:
    """Mock run for self-testing the harness's aggregation logic only.
    NEVER use these numbers in a report or paper -- they are synthetic."""
    time.sleep(0.001)  # simulate a trivial amount of wall-clock work
    jitter = random.uniform(-0.05, 0.05)
    return RunMetrics(
        config_name=config_name,
        ttft_ms=base_ttft_ms * (1 + jitter),
        tokens_per_sec=base_tps * (1 - jitter),
        peak_ram_gb=random.uniform(4.0, 8.0),
        acceptance_rate=random.uniform(0.5, 0.95) if "speculative" in config_name else None,
        notes="MOCK RUN -- self-test only, not a reportable measurement",
    )


def benchmark_config(config_name: str, mock: bool, log_path: str,
                      base_ttft_ms: float = None, base_tps: float = None):
    all_runs = []
    for i in range(WARMUP_RUNS + MEASURED_RUNS):
        if mock:
            run = run_once_MOCK(config_name, base_ttft_ms, base_tps)
        else:
            run = run_once_REAL(config_name, model_path="models/gguf/model-Q4_K_M.gguf")

        if i < WARMUP_RUNS:
            continue  # discard warm-up runs per thermal protocol
        all_runs.append(run)

    save_runs_jsonl(all_runs, log_path)
    agg = aggregate(all_runs)
    return agg


def selftest():
    print("== Benchmark harness self-test (MOCK mode, synthetic numbers) ==\n")
    log_path = "experiments/results/selftest_runs.jsonl"

    configs = [
        ("plain_decoding", 450.0, 12.0),
        ("standard_speculative_decoding", 300.0, 22.0),
        ("plain_cascading", 600.0, 10.0),
        ("safe_core_dialogue_act_exit", 280.0, 24.0),
        ("pads_pause_time_trigger", 210.0, 26.0),
    ]

    for name, ttft, tps in configs:
        agg = benchmark_config(name, mock=True, log_path=log_path, base_ttft_ms=ttft, base_tps=tps)
        print(f"[{agg.config_name}]")
        print(f"  n_runs={agg.n_runs}  TTFT={agg.ttft_ms_mean:.1f}±{agg.ttft_ms_ci95:.1f} ms"
              f"  tok/s={agg.tokens_per_sec_mean:.1f}±{agg.tokens_per_sec_ci95:.1f}"
              f"  peak_RAM={agg.peak_ram_gb_max:.2f} GB"
              f"  acceptance={agg.acceptance_rate_mean}")
        print()

    print("Self-test complete. Aggregation/logging logic verified.")
    print("NONE of the numbers above are real -- rerun with --real on the")
    print("Latitude 5490 once run_once_REAL() is wired to the actual pipeline.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true",
                         help="Run harness self-test with mock timing (safe anywhere)")
    args = parser.parse_args()

    if args.selftest:
        selftest()
    else:
        print("Real-hardware mode requires run_once_REAL() to be implemented")
        print("against the actual llama.cpp / PADS pipeline. Use --selftest")
        print("to verify the harness logic itself first.")
