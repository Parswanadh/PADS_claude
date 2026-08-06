"""
GO/NO-GO TEST #2 -- Real pause-duration feasibility check.

REQUIRES TARGET HARDWARE for the "measured decode-step time" half, and a real
conversational corpus (Switchboard / CallHome) for the "real pause durations" half.
This script is written to run end-to-end once both inputs are available; in this
sandbox it runs in --demo mode against synthetic placeholder numbers so the
comparison logic itself is verified before you plug in real data.

KILL SIGNAL: median real pause duration < time to complete one meaningful
speculative-depth step on this hardware -> the core PADS timing premise is
infeasible as designed; redesign (e.g. exploit only the longest pauses, or
reduce the depth-extension granularity) rather than just re-tuning thresholds.
"""
import argparse
import json
import statistics
import sys


def load_pause_durations(path):
    """Expects a JSON list of floats (seconds) extracted from a corpus's
    turn-transition annotations (e.g. Switchboard-DAMSL silence gaps)."""
    with open(path) as f:
        return json.load(f)


def load_decode_step_times(path):
    """Expects a JSON list of floats (seconds): measured wall-clock time for
    one 'meaningful speculative-depth step' (e.g. extending from the shallow
    exit layer to full depth for one token) on the actual target hardware."""
    with open(path) as f:
        return json.load(f)


def evaluate(pause_durations, decode_step_times):
    median_pause = statistics.median(pause_durations)
    median_step = statistics.median(decode_step_times)
    feasible_fraction = sum(1 for p in pause_durations if p >= median_step) / len(pause_durations)

    print(f"Median real pause duration:      {median_pause*1000:.1f} ms")
    print(f"Median depth-extension step time: {median_step*1000:.1f} ms")
    print(f"Fraction of pauses long enough to fit one step: {feasible_fraction*100:.1f}%")

    if median_pause < median_step:
        print("\nKILL SIGNAL FIRED: median pause shorter than one meaningful step.")
        print("Log as: Test 2: FAILED -> redesign timing granularity, do not just re-tune.")
        return False
    else:
        print("\nPremise holds at the median. Still check the full distribution --")
        print("a low feasible_fraction means the technique only helps on a subset of turns,")
        print("which is a legitimate, reportable finding either way.")
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pauses", help="JSON file of real pause durations (seconds)")
    parser.add_argument("--steps", help="JSON file of measured depth-extension step times (seconds)")
    parser.add_argument("--demo", action="store_true", help="Run with synthetic placeholder data")
    args = parser.parse_args()

    if args.demo or not (args.pauses and args.steps):
        print("[DEMO MODE] Using synthetic placeholder data -- replace with real")
        print("Switchboard/CallHome pause data and real on-hardware step timings")
        print("before this result is reportable.\n")
        synthetic_pauses = [0.18, 0.22, 0.31, 0.45, 0.19, 0.27, 0.5, 0.15, 0.38, 0.29]
        synthetic_steps = [0.09, 0.11, 0.10, 0.12, 0.095, 0.105, 0.10, 0.11, 0.098, 0.10]
        ok = evaluate(synthetic_pauses, synthetic_steps)
    else:
        pauses = load_pause_durations(args.pauses)
        steps = load_decode_step_times(args.steps)
        ok = evaluate(pauses, steps)

    sys.exit(0 if ok else 1)
