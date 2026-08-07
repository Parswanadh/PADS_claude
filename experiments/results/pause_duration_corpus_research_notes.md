# Go/No-Go Test 2 — pause-duration corpus research notes (2026-08-07)

Test 2 (`experiments/go_no_go/test2_pause_duration_check.py`) needs two real
inputs: (a) real turn-transition pause durations from Switchboard/CallHome,
and (b) real measured decode-step time on this hardware. This session
investigated (a) only, without a working model to produce (b) — that half
is separately blocked on the same Hugging Face gated-access issue as model
acquisition (see `model_acquisition_plan.md`).

## Raw corpus access

Switchboard and CallHome are both distributed by the LDC (Linguistic Data
Consortium) and require a paid/institutional license to obtain the raw
audio + annotations needed to compute pause durations directly. No LDC
credentials or access were found configured on this machine or referenced
anywhere in the repo. **This is a real, separate access blocker**, parallel
in kind to the Hugging Face gate on the model weights — it needs either an
LDC subscription (the user's institution may already have one; worth
asking) or a specific freely-available derivative dataset that already
contains this timing information.

## Literature search for a citable summary statistic — inconclusive, and one near-miss caught

Searched for published Switchboard-specific gap/pause-duration statistics
as a stand-in reference while raw corpus access is unresolved. This did
**not** turn up a verified Switchboard-specific number, and surfaced one
attribution that turned out to be wrong on closer inspection — worth
recording so nobody reuses it by accident:

- An initial web search summary claimed a paper ("Timing in turn-taking and
  its implications for processing models of language", Frontiers in
  Psychology 2015) reported "median gap duration 389ms" for the Switchboard
  corpus. **Fetching the actual paper directly showed this is wrong**: that
  paper's Switchboard analysis section only reports **overlap** statistics,
  explicitly stating gap duration alone is not separately reported for
  Switchboard in that paper. The paper does cite gap-duration figures from
  Brady (1968) and Heldner & Edlund (2010) for *other* corpora — the
  394ms-ish number the search engine surfaced looks like a synthesis
  artifact conflating those citations with Switchboard itself.
- Followed the trail to Heldner & Edlund (2010), "Pauses, gaps and overlaps
  in conversations" (*Journal of Phonetics* 38, 555–568) — fetched the PDF
  directly and read it. **This paper also does not analyze Switchboard or
  CallHome.** Its three primary corpora are the Spoken Dutch Corpus
  (telephone + face-to-face Dutch), the HCRC Map Task Corpus (Scottish
  English), and the Swedish Map Task Corpus. None is American English
  telephone conversation, none is Switchboard/CallHome.
- That paper's Table 1 is itself a *literature-review compilation* of gap
  durations from other, older, smaller English-language studies (not
  Switchboard): Norwich & Murphy (1938, mean 410ms/median 320ms), Brady
  (1968, mean 345ms/median 264ms), Beattie & Barnard (1979, two studies:
  mean 507/median 400ms and mean 474/median 333ms), Jaffe & Feldstein
  (1970, mean 664ms, eye-contact condition), Sellen (1995, mean 480ms no
  eye contact / mean 575ms–median 360ms eye contact), Weilhammer & Rabold
  (2003, mean 404ms), Bull (1996, mean 384ms/median 355ms). These are
  small, methodologically disparate studies (several require face-to-face
  eye contact, which doesn't even apply to a telephone corpus), spanning
  1938–2003 — none are Switchboard, none should be cited as if they were.

**Conclusion: no verified Switchboard/CallHome-specific pause-duration
statistic has been found.** The cross-study English gap-duration figures
above (unrelated corpora, means roughly 340–660ms, medians roughly
260–400ms) are at best a very rough sanity-check range for "this is the
right order of magnitude for human turn-transition gaps," not a citable
Switchboard number, and must not be plugged into Test 2 as if they were
real Switchboard data. `test2_pause_duration_check.py` should keep running
in `--demo` mode with its clearly-labeled synthetic placeholders until
genuine data is available.

## Path forward

1. Ask the user whether their institution already has LDC access (fastest
   path if so — check before assuming it needs to be purchased).
2. If not, search more specifically for a paper that computes gap/pause
   statistics *from Switchboard itself* (e.g., work explicitly using the
   NXT Switchboard Annotations, LDC2009T26, which has a more permissive
   CC-BY-NC-SA license per this session's earlier search — still needs
   verifying whether it includes timing data usable without the base
   audio). Not attempted this session — a distinct next unit of work.
3. Either way, the decode-step-time half of Test 2 stays blocked until the
   model-acquisition blocker (`model_acquisition_plan.md`) is resolved, so
   Test 2 cannot fully complete even once a real pause-duration number is
   found.
