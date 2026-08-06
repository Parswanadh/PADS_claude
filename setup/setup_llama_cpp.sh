#!/usr/bin/env bash
# Environment setup for the Dell Latitude 5490 (CPU-only, no CUDA/Metal flags).
# REQUIRES TARGET HARDWARE — running this in a generic sandbox is fine for a
# syntax/dry-run check, but the resulting binaries must be rebuilt and
# benchmarked ON THE ACTUAL LAPTOP for any reported number to be valid.
set -euo pipefail

echo "== HNIA/PADS: llama.cpp CPU-only setup =="

if [ ! -d "llama.cpp" ]; then
  git clone https://github.com/ggml-org/llama.cpp
fi
cd llama.cpp

# CPU-only build — no GGML_CUDA / GGML_METAL flags on the Latitude 5490.
# Enable native CPU optimizations (AVX2/AVX-512 if the 8th-gen CPU supports it).
# -DLLAMA_BUILD_UI=OFF skips the embedded npm-based web UI (server-only
# feature, irrelevant to CLI/headless inference, and needlessly slow to
# build) -- verified via an actual build attempt, see
# experiments/results/llamacpp_build_verification_log.md
cmake -B build -DGGML_NATIVE=ON -DCMAKE_BUILD_TYPE=Release -DLLAMA_BUILD_UI=OFF

# Conservative thread count per CLAUDE.md's safety rule: nproc-1, not nproc,
# to leave headroom for the OS and any other foreground process.
NPROC="$(nproc)"
BUILD_JOBS=$(( NPROC > 1 ? NPROC - 1 : 1 ))
cmake --build build --config Release -j "$BUILD_JOBS"

echo "Build complete. Binaries in llama.cpp/build/bin/"
echo ""
echo "Next: place a GGUF model (see experiments/go_no_go/test1_bandwidth_vs_compute.sh"
echo "header for the recommended starter checkpoint), then run the Go/No-Go suite."
echo ""
echo "Quantize down from F16, never from an already-quantized file:"
echo "  ./build/bin/llama-quantize model-f16.gguf model-Q4_K_M.gguf Q4_K_M"
