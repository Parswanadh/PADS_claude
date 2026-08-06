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

## Current status: BLOCKED on a human action, as of 2026-08-07

Checked whether this machine's existing Hugging Face login (`hf auth
whoami` → account `Havoc1904`, already authenticated from unrelated prior
use — confirmed via `~/.cache/huggingface/token` and existing cached models
for other projects) already has gated access to this specific repo, by
attempting to download only the small `config.json`/`README.md` files
(not the full ~2GB weights) as a lightweight access test:

```
$ hf download facebook/layerskip-llama3.2-1B config.json README.md
Error: Access denied. This repository requires approval.
```

**This is a genuine blocker, not a fabricated or worked-around result.**
Gated HF repos require a human to visit the model page while logged in and
click through the license acceptance form — this cannot be done
programmatically or on the user's behalf.

### Action required (human, not Claude Code)

Visit https://huggingface.co/facebook/layerskip-llama3.2-1B while logged in
as the `Havoc1904` HF account (the account already authenticated on this
machine) and accept the FAIR Noncommercial Research License. Access is
typically granted within minutes to a few hours after acceptance (Meta's
side, not something to poll aggressively for).

### Next step once access is granted (a future session)

```
mkdir -p models/checkpoints
hf download facebook/layerskip-llama3.2-1B --local-dir models/checkpoints/layerskip-llama3.2-1B
```

Then verify the download (file sizes match the ~2GB expected, safetensors
load cleanly), before proceeding to GGUF conversion
(`convert_hf_to_gguf.py ... --outtype f16`) and quantization
(`llama-quantize model-f16.gguf model-Q4_K_M.gguf Q4_K_M`) per
`docs/03_SKILL.md` §1 — quantize last, never from an already-quantized
file. `models/` should be added to `.gitignore` at that point (large binary
weights don't belong in git).
