# CLAUDE.md — PADS project operating rules

This file persists the safety constraints, delegation rules, and build order
for every future session on this repo. Read this before doing anything else.
It supersedes re-pasting these rules in each prompt.

## What this project is

Pause-Aware Depth Scheduling (PADS): CPU-only edge conversational inference
via self-speculative early-exit. Full spec lives in `docs/`. **Read
`docs/03_SKILL.md` before writing or running anything** — it defines what NOT
to build (no two-model router, no cross-model KV-cache handoff, no
from-scratch foundation model training) and the mandatory build order.

## Target hardware discrepancy — read this before trusting any number

The docs (`README.md`, `docs/03_SKILL.md`) specify the target hardware as a
**Dell Latitude 5490, 16GB RAM, no discrete GPU**. The machine this repo is
actually being developed/run on as of 2026-08-07 is an **Alienware m16 R2**
(Intel Core Ultra 7 155H, 22 threads, ~15GB RAM) — a different machine.

**Any benchmark number measured on this Alienware machine is a dev/pipeline
verification number, not a reportable target-hardware number.** Label it as
such in every log and never let it flow into `paper/PADS_manuscript.tex`
Section V as if it were measured on the Latitude 5490. If/when the Latitude
5490 becomes available, re-run the Go/No-Go suite and benchmarks there before
reporting anything in the paper.

## Hard safety constraint — overrides progress speed

This machine must never crash, freeze, thrash, or become unresponsive. Equal
priority to correctness.

- Before any command that loads a model, compiles code, trains something, or
  invokes agy: check `free -h` (use the **available** column, not `free`) and
  `df -h`. If available RAM is below ~3GB or free disk is below ~5GB, STOP
  and log why instead of proceeding.
- Also check `vmstat 1 5` for active `si`/`so` swap churn if swap usage looks
  high. A high but static swap watermark (no active paging) is not itself a
  blocker; active thrashing is.
- Never run more than one heavy process at a time, full stop — this includes
  agy. Claude Code and agy must never both be executing something heavy
  simultaneously. If you delegate to agy, wait for it to finish before doing
  anything else compute-heavy yourself.
- Wrap every potentially long-running or hangable command in `timeout` (e.g.
  `timeout 600 <command>`). A timeout firing is a signal to stop and
  investigate, never to blindly retry at the same intensity.
- Start with conservative thread counts (`nproc - 1`) and only scale up after
  confirming stability across a full run. `nproc` on this machine is 22, so
  start at 21 and prefer lower for anything sustained.
- If you observe memory pressure, thermal throttling, swap activity, or any
  instability: STOP the current operation immediately, log it in the
  relevant results file, commit the current state, and end the turn. Do not
  push through.

## Delegating to agy

agy is available headlessly:

```
agy -p "<task>" --model gemini-3.6-flash-high --sandbox --dangerously-skip-permissions --output-format text
```

Confirmed via `agy models` on 2026-08-07 — `gemini-3.6-flash-high` is the
literal model identifier for "gemini 3.6 flash" at high effort (the model
list already encodes effort as a suffix: `-high`/`-medium`/`-low`). Don't
guess this string; re-run `agy models` if it's ever unclear.

Use agy for **content and code generation only**, never for the
safety-critical execution itself:

- Good: writing a training script against a spec, generating unit tests,
  summarizing a raw log into a short report, drafting boilerplate.
- Not allowed via agy: actually running model inference, compiling
  llama.cpp, running a Go/No-Go test, or anything that loads a model into
  memory or sustains CPU load. That execution stays with Claude Code, under
  its own safety checks, one heavy process at a time — agy generates, Claude
  runs and verifies.

Every agy output must be reviewed before it's accepted: read it, check it
against `docs/03_SKILL.md`'s rules (no fabricated numbers, no skipped
baselines, no KV-cache handoff between differently-sized models), and only
then integrate and commit it. Never commit agy's output unread.

## Build order (do not reorder — full detail in docs/03_SKILL.md §3)

1. Environment setup (`setup/setup_llama_cpp.sh`, `setup/requirements.txt`).
2. Go/No-Go tests 1–7, run on real hardware, every result logged in
   `experiments/go_no_go_results.md` — including honest failures. Do not
   proceed past this phase until all seven have a logged result.
3. Safe-core pipeline (plain self-speculative early-exit decoding) + the
   four local baselines, only once Go/No-Go is fully logged.
4. Dialogue-act exit policy classifier.
5. Stretch layer (turn-taking predictor + pause-time trigger, PADS proper),
   only once 1–4 are stable and benchmarked. If it shows no measurable gain
   by the internal month-4 checkpoint, stop iterating and report the
   safe-core result with the stretch layer written up as a negative result.

Never skip a phase because "it'll probably work" — see
`docs/01_HNIA_PADS_Detailed_Report.md` §5–6 for why each Go/No-Go test
exists.

## Commit and logging discipline

- Commit after every atomic unit of work. Small, frequent, revertible
  commits — a crash should never lose more than a few minutes of work.
- Push to GitHub (`origin`, via `git push` — `gh auth` is already configured
  as the credential helper) promptly after each commit, not batched up.
- Never fabricate a benchmark number. If something can't be measured yet,
  say so explicitly in the log.
- At the end of every session, append a short entry to `PROGRESS.md`: what
  was done, what passed/failed, what's next, any safety events, and which
  steps (if any) were delegated to agy. Commit and push it.
