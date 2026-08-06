"""
PADS trigger policy: decides, per streaming partial-utterance update, whether
to speculatively begin full-depth computation during the pause.

This module is hardware-agnostic and fully testable without the target
laptop or real models -- it operates purely on the two probability signals
that upstream components (turn-taking predictor, dialogue-act classifier)
produce. Verified with the accompanying test suite in this sandbox.

Design principle (Report Sec 4.1, PRD Sec 9): the threshold must be
CONSERVATIVE and ASYMMETRIC -- false triggers should be cheap, true triggers
should be common. Do not tune this for raw classification accuracy; tune it
for the trigger's cost asymmetry.
"""
from dataclasses import dataclass
from enum import Enum


class Decision(Enum):
    STAY_SHALLOW = "stay_shallow"
    TRIGGER_DEEP = "trigger_deep"


@dataclass
class TriggerPolicyConfig:
    turn_ending_threshold: float = 0.75   # P(turn ending soon) must exceed this
    deep_need_threshold: float = 0.65     # P(needs deep reasoning) must exceed this
    # Both must clear their threshold -- this is the "asymmetric, conservative"
    # AND-gate described in the Report; do not relax to an OR-gate without
    # re-deriving the cost asymmetry, since an OR-gate roughly doubles the
    # false-trigger rate for a linear gain in true-trigger rate.


@dataclass
class TriggerDecisionLog:
    turn_ending_prob: float
    deep_need_prob: float
    decision: Decision


class TriggerPolicy:
    def __init__(self, config: TriggerPolicyConfig = None):
        self.config = config or TriggerPolicyConfig()
        self.history: list[TriggerDecisionLog] = []

    def decide(self, turn_ending_prob: float, deep_need_prob: float) -> Decision:
        if not (0.0 <= turn_ending_prob <= 1.0):
            raise ValueError(f"turn_ending_prob out of range: {turn_ending_prob}")
        if not (0.0 <= deep_need_prob <= 1.0):
            raise ValueError(f"deep_need_prob out of range: {deep_need_prob}")

        if (turn_ending_prob >= self.config.turn_ending_threshold
                and deep_need_prob >= self.config.deep_need_threshold):
            decision = Decision.TRIGGER_DEEP
        else:
            decision = Decision.STAY_SHALLOW

        self.history.append(TriggerDecisionLog(turn_ending_prob, deep_need_prob, decision))
        return decision

    def resolve(self, decision_index: int, turn_actually_ended: bool, actually_needed_deep: bool) -> str:
        """Call once the true outcome is known, to classify the decision as
        correct-trigger / false-trigger / correct-shallow / missed-trigger.
        This feeds acceptance-rate and false-trigger-rate reporting."""
        log = self.history[decision_index]
        if log.decision == Decision.TRIGGER_DEEP:
            if turn_actually_ended and actually_needed_deep:
                return "correct_trigger"
            else:
                return "false_trigger"  # discarded speculative branch -- must be cheap
        else:
            if turn_actually_ended and actually_needed_deep:
                return "missed_trigger"  # no speedup gained, but no waste either
            else:
                return "correct_shallow"

    def stats(self) -> dict:
        total = len(self.history)
        triggers = sum(1 for h in self.history if h.decision == Decision.TRIGGER_DEEP)
        return {
            "total_decisions": total,
            "trigger_rate": triggers / total if total else 0.0,
        }
