"""
GO/NO-GO TEST #2 helper -- measures real decode-step (depth-extension) times.

Runs the actual LayerSkip self-speculative pipeline against a real checkpoint
and captures wall-clock time for each forward_remainder() call (extending
drafted tokens from the shallow exit layer to full depth for verification) --
this is "one meaningful speculative-depth step" per
experiments/go_no_go/test2_pause_duration_check.py's --steps input format.

Requires the instrumentation patch in self_speculation/self_speculation_generator.py
(DEPTH_EXTENSION_STEP_TIMES_SEC) -- see
experiments/results/layerskip_python314_transformers450_compat.patch in this
repo for the full set of compatibility patches this also depends on.

This measures the OTHER half of Test 2 (decode-step timing on real hardware).
It does NOT measure real human pause durations -- that half still needs a
real conversational corpus (Switchboard/CallHome, LDC-gated) or a verified
alternative source. Do not treat this script's output as a complete Test 2
result on its own.

Usage (from the LayerSkip/ directory, with .venv-layerskip active):
    RANK=0 WORLD_SIZE=1 LOCAL_RANK=0 MASTER_ADDR=localhost MASTER_PORT=29501 \
        ../.venv-layerskip/bin/python \
        ../experiments/go_no_go/test2_measure_decode_step_times.py \
        --model ../models/checkpoints/layerskip-llama3.2-1B \
        --data_path ../experiments/results/test3_conversational_prompts.jsonl \
        --exit_layer 3 --num_speculations 6 \
        --output ../experiments/results/test2_decode_step_times.json
"""
import argparse
import json
import os
import sys

import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../../LayerSkip")

import generate  # noqa: E402
from self_speculation import self_speculation_generator  # noqa: E402
from self_speculation.generator_base import (  # noqa: E402
    GenerationConfig,
    HuggingfaceLlamaGenerator,
)
from self_speculation.self_speculation_generator import (  # noqa: E402
    SelfSpeculativeGenerationStrategy,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--data_path", required=True)
    parser.add_argument("--exit_layer", type=int, required=True)
    parser.add_argument("--num_speculations", type=int, required=True)
    parser.add_argument("--max_steps", type=int, default=64)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    os.environ.setdefault("RANK", "0")
    os.environ.setdefault("WORLD_SIZE", "1")
    os.environ.setdefault("LOCAL_RANK", "0")
    os.environ.setdefault("MASTER_ADDR", "localhost")
    os.environ.setdefault("MASTER_PORT", "29501")

    class Args:
        model = args.model
        seed = 42

    device = "cuda" if torch.cuda.is_available() else "cpu"
    generate.setup(Args(), device=device)
    model, tokenizer = generate.load_model_and_tokenizer(Args(), device=device)

    generator = HuggingfaceLlamaGenerator(
        tokenizer=tokenizer,
        model=model,
        generation_strategy=SelfSpeculativeGenerationStrategy(),
    )
    generation_config = GenerationConfig(
        max_steps=args.max_steps,
        exit_layer=args.exit_layer,
        num_speculations=args.num_speculations,
        generation_strategy="self_speculative",
        sample=False,
    )

    prompts = pd.read_json(args.data_path, lines=True)["prompt"].tolist()
    for prompt in prompts:
        generator.generate(prompt=prompt, generation_config=generation_config)

    step_times = self_speculation_generator.DEPTH_EXTENSION_STEP_TIMES_SEC
    print(f"Captured {len(step_times)} depth-extension step timings.")
    print(f"min={min(step_times):.4f}s max={max(step_times):.4f}s "
          f"mean={sum(step_times)/len(step_times):.4f}s")

    with open(args.output, "w") as f:
        json.dump(step_times, f, indent=2)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
