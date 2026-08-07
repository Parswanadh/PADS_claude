# llama.cpp inference pipeline smoke test (2026-08-07)

## Why

Earlier sessions verified `llama-cli`/`llama-quantize` compile and that
`llama-cli --version` runs, but never verified the build can actually
**load a model and generate tokens** — the real inference pipeline was
untested. The actual LayerSkip checkpoint
(`facebook/layerskip-llama3.2-1B`, see `model_acquisition_plan.md`) is
still gated pending a human accepting Meta's license, so this session used
a small, definitively **ungated** stand-in model to verify the pipeline
mechanics independently of that blocker.

**This is not a Go/No-Go test result.** It uses a different model
(TinyLlama-1.1B-Chat, not LayerSkip) purely to verify the llama.cpp build
and invocation flow work end-to-end on this hardware. None of these numbers
should be read as PADS performance data.

## What was done

- Verified `TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF` is ungated (small
  metadata-file test download succeeded).
- Checked file sizes from the model card before downloading: `Q4_K_M`
  quant, 0.67GB, ~3.17GB max RAM — comfortably within this machine's
  budget. Downloaded it (668,788,096 bytes) into `models/smoke_test/`
  (gitignored — `models/` added to `.gitignore` this session, large binary
  weights don't belong in git).
- Ran `llama-cli` with the downloaded GGUF, conservative thread count
  (`-t 21`, nproc-1), wrapped in `timeout`.

## A real gotcha found — document for the future benchmark harness

First attempt (`-no-cnv --simple-io < /dev/null`, `timeout 60`) **did not
exit cleanly**: the CLI still auto-entered conversation mode (this build's
default is "auto enabled if chat template is available," and TinyLlama-Chat
has one), generated a correct response, then dropped into an interactive
loop reading further "turns" from stdin. With stdin redirected from
`/dev/null` (which is immediately EOF, not a clean terminate signal to this
loop), it looped printing empty `>` prompts until the timeout killed it at
60s — producing a runaway 4.2GB log file (cleaned up immediately after).
This is exactly the kind of thing CLAUDE.md's "a timeout firing is a signal
to stop and investigate, never blindly retry" rule is for — investigated
via `llama-cli --help` rather than re-running the same command harder.

**Fix:** `-st` / `--single-turn` is the correct flag — per `--help`: "run
conversation for a single turn only, then exit when done; will not be
interactive if first turn is predefined with `--prompt`." Retried with
`-st` (`timeout 30`, still `< /dev/null` as a defensive stdin guard):
**exited cleanly with code 0** after generating.

**Action for `src/eval/benchmark_harness.py` and any future llama-cli
automation: always pass `-st` (or `-no-cnv` verified insufficient alone)
when scripting non-interactive generation with this llama.cpp build,
especially for chat-template models.** Note this in the harness when it's
built.

## Result: pipeline genuinely works

```
$ ./build/bin/llama-cli -m models/smoke_test/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
    -p "The capital of France is" -n 32 -t 21 -st < /dev/null
...
> The capital of France is
Yes, the capital of France is Paris.

[ Prompt: 232.9 t/s | Generation: 59.0 t/s ]

Exiting...
```

Exit code 0, ran twice with consistent results across the two successful
attempts (232.9–268.2 t/s prompt, 57.1–59.0 t/s generation — the first
successful number came from the `-no-cnv` attempt's initial correct
generation before it looped, captured in that run's log before cleanup).
RAM stayed at 7.5–7.7GB available throughout; no memory pressure at any
point during model load or generation.

**This confirms the compiled `llama-cli` binary can actually load a real
GGUF model and generate coherent text on this hardware** — the missing
piece of verification from the compile-only sessions. When the LayerSkip
checkpoint becomes available, the pipeline mechanics (invocation, threading,
non-interactive flags) are now known-working, isolating any future issue to
be about the specific model/config rather than the harness itself.

## Cleanup

The TinyLlama GGUF file (638MB) is left in `models/smoke_test/` (gitignored)
for any future quick smoke tests — not deleted, since it's small and
useful, but clearly separated from the eventual real LayerSkip checkpoint
directory (`models/checkpoints/`, per `model_acquisition_plan.md`).
