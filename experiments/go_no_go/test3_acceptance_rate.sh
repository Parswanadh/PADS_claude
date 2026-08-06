#!/usr/bin/env bash
# GO/NO-GO TEST #3 -- Off-the-shelf acceptance rate check
# REQUIRES TARGET HARDWARE + a public LayerSkip checkpoint
# (github.com/facebookresearch/LayerSkip -- e.g. facebook/layerskip-llama2-7B)
#
# Run the checkpoint's own self-speculative generation strategy, UNMODIFIED,
# on conversational-style prompts, and read off the acceptance rate the
# LayerSkip benchmark script reports. Do this BEFORE any custom fine-tuning
# or quantization -- this is the ceiling; your own pipeline will not exceed it.
#
# KILL SIGNAL: acceptance rate too low to matter (well below the ~90%+ figures
# reported in GPU papers) -> flag before months of custom training are spent
# trying to fix a problem that starts at the checkpoint level.
set -euo pipefail

echo "== Go/No-Go Test 3: off-the-shelf LayerSkip acceptance rate =="
echo "Prerequisite: clone github.com/facebookresearch/LayerSkip and follow its"
echo "README to download a checkpoint (e.g. facebook/layerskip-llama2-7B)."
echo ""
echo "Example invocation (from within the LayerSkip repo):"
echo "  torchrun benchmark.py --model facebook/layerskip-llama2-7B \\"
echo "    --dataset cnn_dm_summarization \\"
echo "    --num_samples 50 \\"
echo "    --generation_strategy self_speculative \\"
echo "    --exit_layer 8 --num_speculations 6 \\"
echo "    --output_dir experiments/results/test3_acceptance"
echo ""
echo "Substitute a conversational-style prompt set for --dataset if possible --"
echo "the reported acceptance rate is dataset-dependent, and conversational"
echo "turns are the actual target distribution for this project, not summarization."
echo ""
echo "Log the resulting acceptance rate in experiments/go_no_go_results.md."
