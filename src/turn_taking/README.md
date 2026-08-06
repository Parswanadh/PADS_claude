# Turn-Taking Predictor — Integration Point

**Not implemented in this sandbox.** Requires real or recorded conversational
audio and an audio-capable environment, neither of which is appropriate to
fabricate here. This is the integration contract the rest of the pipeline
expects, so implementation can proceed directly once real audio is available.

## Recommended approach (per Reading List item 17–18)

Use a CPU-capable Voice Activity Projection (VAP) model, or a lightweight
purpose-built turn-taking model (e.g., Krisp's ~6M-parameter reference
architecture) rather than building one from scratch. Both are documented
to run in real time on CPU.

## Required interface

```python
class TurnTakingPredictor:
    def update(self, audio_chunk: bytes) -> float:
        """
        Called on each streaming audio chunk. Returns P(turn ending within
        the next ~300ms) as a float in [0, 1]. This is the turn_ending_prob
        signal consumed by src/trigger_policy/policy.py's TriggerPolicy.decide().
        """
        raise NotImplementedError
```

## Data needed before this can be built and evaluated

- Real or recorded conversational audio with natural pauses/disfluencies
  (Switchboard, CallHome, or project-collected recordings).
- Ground-truth turn-boundary annotations, for evaluating predictor accuracy
  and for Go/No-Go Test #2's pause-duration statistics.

## What NOT to do

- Do not approximate this with a fixed silence-threshold VAD as the final
  design — that reintroduces the "long pauses, delayed responses" problem
  the predictive-turn-taking literature (item 17) specifically improves on.
  A fixed-threshold VAD is acceptable ONLY as a quick placeholder to unblock
  early integration testing of the rest of the pipeline, clearly labeled as such.
