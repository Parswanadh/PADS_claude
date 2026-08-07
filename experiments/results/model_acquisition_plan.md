# Model acquisition plan — starting checkpoint decision

## Chosen checkpoint: `facebook/layerskip-llama3.2-1B`

Verified directly (Hugging Face model card fetched and read, not guessed
from memory) on 2026-08-07:

- **Architecture:** Llama 3.2, 1B parameters, continually pretrained with
  LayerSkip (early-exit loss + layer dropout), from Meta/FAIR — the
  official LayerSkip authors, not a third-party re-quantization.
- **Format:** safetensors, BF16, ~2GB on disk.
- **Model type:** base model, not instruction-tuned.
- **License:** FAIR Noncommercial Research License — restricted to
  noncommercial research/education/analysis use, which fits this project
  (an academic paper submission). Explicitly prohibits commercial use,
  weapons development, deceptive practices.
- **Access:** **Gated.** Requires a Hugging Face account to accept Meta's
  license agreement and share contact info with Meta before any file in
  the repo can be downloaded.
- Self-speculative decoding usage is documented directly on the model card
  (HF `transformers`-based shared-weight-clone method, or the LayerSkip
  GitHub codebase with `--generation_strategy self_speculative --exit_layer 3`).

## Why 1B, not the also-released 7B/8B/70B LayerSkip checkpoints

Meta has also released `layerskip-llama2-7B`, `layerskip-llama3-8B`,
`layerskip-codellama-7B`, and `layerskip-llama2-70B`. The 1B variant was
chosen deliberately:

- It comfortably fits this machine's RAM budget (Go/No-Go Test 5 found
  ~13GB usable pipeline budget under a conservative 3GB OS headroom on this
  ~15GB-RAM dev machine — a 7B+ model in F16 alone would already consume
  most of that before the dialogue-act classifier or turn-taking predictor
  ever load).
- `docs/03_SKILL.md`'s Go/No-Go Test 1 kill signal is specifically about
  this hardware being memory-bandwidth-bound; starting small keeps the
  safe-core pipeline's first real benchmark honest and fast to iterate on,
  with room to scale up to a larger checkpoint later if the small one's
  numbers justify it.
- It's still an official Meta/FAIR release with the documented LayerSkip
  recipe applied, not a compromise on "start from released checkpoints,
  don't train from scratch."

## Current status: request submitted, awaiting Meta's manual review (as of 2026-08-07)

Initial state was blocked on the user needing to visit the model page and
submit the access request — that step is now done. The user confirmed
(pasting the actual model page content) that the request has been
**submitted** and the page shows: "Your request to access this repository
has been submitted and is awaiting a review from the repository authors."
This is a gated repo with **human review on Meta's side**, not an
instant-accept gate — approval timing is now out of both the user's and
Claude Code's hands.

Re-verified directly (not just trusting the pasted page text) — as of the
last check this session, access is still denied:

```
$ hf download facebook/layerskip-llama3.2-1B config.json
Error: Access denied. This repository requires approval.
```

The user also supplied two different HF tokens directly in chat at
different points; both resolved via `hf auth whoami` to the same
`Havoc1904` account already tried, and neither changed the access result —
**a token cannot bypass a pending gated-repo review**, so this confirms the
blocker is genuinely "waiting on Meta," not a credentials issue. (Both
tokens were used only as one-shot `HF_TOKEN=... hf download` environment
variables, never written to any file or persisted config, and never
committed anywhere.)

### Prep work done while waiting (2026-08-07)

Rather than poll idly, set up the GGUF conversion environment now so
there's no additional setup delay once access clears. `convert_hf_to_gguf.py`
needs `torch`, `transformers==4.57.6`, `sentencepiece`, `gguf`, `protobuf`,
and a pinned `numpy~=1.26.4` — the last of which conflicts with the newer
numpy already in the main `.venv` (installed for the sklearn-based
scripts). Created a **separate** venv, `.venv-convert/` (gitignored), and
installed `llama.cpp/requirements/requirements-convert_hf_to_gguf.txt`
into it — confirmed working via `convert_hf_to_gguf.py --help` (exit 0).
RAM stayed flat throughout install (mostly download/unpack, not
compute-heavy); disk usage ~1GB for the full torch-CPU + transformers
stack, well within budget.

### Next step once access is granted (a future session)

```
mkdir -p models/checkpoints
hf download facebook/layerskip-llama3.2-1B --local-dir models/checkpoints/layerskip-llama3.2-1B
```

Then verify the download (file sizes match the ~2GB expected, safetensors
load cleanly), before proceeding to GGUF conversion using the now-ready
`.venv-convert`:

```
.venv-convert/bin/python llama.cpp/convert_hf_to_gguf.py \
  models/checkpoints/layerskip-llama3.2-1B --outtype f16 \
  --outfile models/gguf/layerskip-llama3.2-1b-f16.gguf
```

Then quantize with the already-built `llama-quantize`
(`llama.cpp/build/bin/llama-quantize model-f16.gguf model-Q4_K_M.gguf
Q4_K_M`) per `docs/03_SKILL.md` §1 — quantize last, never from an
already-quantized file.
