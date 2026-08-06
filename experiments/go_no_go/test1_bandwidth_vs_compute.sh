#!/usr/bin/env bash
# GO/NO-GO TEST #1 — Bandwidth-vs-compute check
# REQUIRES TARGET HARDWARE (Dell Latitude 5490) + a real GGUF model.
#
# Recommended starter checkpoint: a 7-9B instruct model quantized to Q4_K_M,
# e.g. a LayerSkip-recipe Llama checkpoint (github.com/facebookresearch/LayerSkip)
# converted to GGUF, OR any similarly-sized public GGUF for an initial sanity pass
# before the real LayerSkip checkpoint is in place.
#
# KILL SIGNAL: tokens/sec flatlines past 4-5 threads -> memory-bandwidth-bound
# regime confirmed. See Report Sec 5.1/6 for the pivot this implies.
set -euo pipefail

MODEL_PATH="${1:-models/gguf/model-Q4_K_M.gguf}"
LLAMA_CLI="llama.cpp/build/bin/llama-cli"
PROMPT="Explain, in a few sentences, why memory bandwidth can bottleneck CPU-only LLM inference."
OUT="experiments/results/test1_bandwidth_vs_compute.csv"

if [ ! -f "$MODEL_PATH" ]; then
  echo "ERROR: model not found at $MODEL_PATH"
  echo "Place a GGUF model there (see header comment) before running this test."
  exit 1
fi

mkdir -p experiments/results
echo "threads,tokens_per_sec" > "$OUT"

for T in 1 2 3 4 5 6 7 8; do
  echo "== threads=$T =="
  # llama-cli prints a timing summary to stderr; we grep the eval rate line.
  RESULT=$("$LLAMA_CLI" -m "$MODEL_PATH" -p "$PROMPT" -n 128 -t "$T" 2>&1 | tee /dev/stderr)
  TPS=$(echo "$RESULT" | grep -oP 'eval time.*?\K[0-9.]+(?= tokens per second)' | tail -1 || echo "NA")
  echo "$T,$TPS" >> "$OUT"
done

echo ""
echo "Results written to $OUT"
echo "Plot tokens/sec vs threads. If it flatlines past 4-5 threads, the kill"
echo "signal has fired -- log this in experiments/go_no_go_results.md as:"
echo "  Test 1: FAILED (bandwidth-bound) -> pivot to characterization framing / try smaller model"
