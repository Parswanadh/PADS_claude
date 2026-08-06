"""Data structures for one benchmark run's metrics -- shared by the harness
and by any downstream aggregation/plotting script."""
from dataclasses import dataclass, field, asdict
import json
import statistics


@dataclass
class RunMetrics:
    config_name: str
    ttft_ms: float
    tokens_per_sec: float
    peak_ram_gb: float
    acceptance_rate: float | None = None   # None if not applicable (e.g. plain decoding baseline)
    energy_joules: float | None = None     # None if energy tooling unavailable (Go/No-Go test 6)
    notes: str = ""


@dataclass
class MetricsAggregate:
    config_name: str
    n_runs: int
    ttft_ms_mean: float
    ttft_ms_ci95: float
    tokens_per_sec_mean: float
    tokens_per_sec_ci95: float
    peak_ram_gb_max: float
    acceptance_rate_mean: float | None
    energy_joules_mean: float | None


def _ci95(values: list[float]) -> float:
    """Rough 95% CI half-width assuming normality -- adequate for reporting
    at the small-N scale of a two-semester lab benchmark; note this
    approximation explicitly in the paper's methodology section."""
    if len(values) < 2:
        return 0.0
    stdev = statistics.stdev(values)
    return 1.96 * stdev / (len(values) ** 0.5)


def aggregate(runs: list[RunMetrics]) -> MetricsAggregate:
    if not runs:
        raise ValueError("Cannot aggregate an empty run list.")
    config_name = runs[0].config_name
    assert all(r.config_name == config_name for r in runs), "Mixed config names in one aggregate call."

    ttfts = [r.ttft_ms for r in runs]
    tps = [r.tokens_per_sec for r in runs]
    rams = [r.peak_ram_gb for r in runs]
    acc_rates = [r.acceptance_rate for r in runs if r.acceptance_rate is not None]
    energies = [r.energy_joules for r in runs if r.energy_joules is not None]

    return MetricsAggregate(
        config_name=config_name,
        n_runs=len(runs),
        ttft_ms_mean=statistics.mean(ttfts),
        ttft_ms_ci95=_ci95(ttfts),
        tokens_per_sec_mean=statistics.mean(tps),
        tokens_per_sec_ci95=_ci95(tps),
        peak_ram_gb_max=max(rams),
        acceptance_rate_mean=statistics.mean(acc_rates) if acc_rates else None,
        energy_joules_mean=statistics.mean(energies) if energies else None,
    )


def save_runs_jsonl(runs: list[RunMetrics], path: str):
    with open(path, "a") as f:
        for r in runs:
            f.write(json.dumps(asdict(r)) + "\n")


def load_runs_jsonl(path: str) -> list[RunMetrics]:
    runs = []
    with open(path) as f:
        for line in f:
            runs.append(RunMetrics(**json.loads(line)))
    return runs
