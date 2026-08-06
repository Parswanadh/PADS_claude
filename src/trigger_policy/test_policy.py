"""Unit tests for the PADS trigger policy -- run with: pytest test_policy.py -v"""
import pytest
from policy import TriggerPolicy, TriggerPolicyConfig, Decision


def test_default_config_requires_both_signals_high():
    policy = TriggerPolicy()
    # Only turn-ending is high -> should stay shallow
    assert policy.decide(0.9, 0.3) == Decision.STAY_SHALLOW
    # Only deep-need is high -> should stay shallow
    assert policy.decide(0.3, 0.9) == Decision.STAY_SHALLOW
    # Both high -> should trigger
    assert policy.decide(0.9, 0.9) == Decision.TRIGGER_DEEP


def test_boundary_values_are_inclusive():
    config = TriggerPolicyConfig(turn_ending_threshold=0.75, deep_need_threshold=0.65)
    policy = TriggerPolicy(config)
    assert policy.decide(0.75, 0.65) == Decision.TRIGGER_DEEP
    assert policy.decide(0.749, 0.65) == Decision.STAY_SHALLOW


def test_out_of_range_probabilities_raise():
    policy = TriggerPolicy()
    with pytest.raises(ValueError):
        policy.decide(1.5, 0.5)
    with pytest.raises(ValueError):
        policy.decide(0.5, -0.1)


def test_resolve_classifies_outcomes_correctly():
    policy = TriggerPolicy()
    idx0 = 0
    policy.decide(0.9, 0.9)  # will trigger
    assert policy.resolve(idx0, turn_actually_ended=True, actually_needed_deep=True) == "correct_trigger"

    idx1 = 1
    policy.decide(0.9, 0.9)  # triggers again
    assert policy.resolve(idx1, turn_actually_ended=False, actually_needed_deep=True) == "false_trigger"

    idx2 = 2
    policy.decide(0.3, 0.3)  # stays shallow
    assert policy.resolve(idx2, turn_actually_ended=True, actually_needed_deep=True) == "missed_trigger"

    idx3 = 3
    policy.decide(0.3, 0.3)  # stays shallow
    assert policy.resolve(idx3, turn_actually_ended=True, actually_needed_deep=False) == "correct_shallow"


def test_stats_reports_trigger_rate():
    policy = TriggerPolicy()
    policy.decide(0.9, 0.9)   # trigger
    policy.decide(0.9, 0.9)   # trigger
    policy.decide(0.1, 0.1)   # shallow
    policy.decide(0.1, 0.1)   # shallow
    stats = policy.stats()
    assert stats["total_decisions"] == 4
    assert stats["trigger_rate"] == 0.5


def test_asymmetric_thresholds_are_independently_configurable():
    """Confirms the AND-gate cost-asymmetry design isn't accidentally an OR-gate."""
    strict_config = TriggerPolicyConfig(turn_ending_threshold=0.95, deep_need_threshold=0.95)
    policy = TriggerPolicy(strict_config)
    assert policy.decide(0.94, 0.99) == Decision.STAY_SHALLOW
    assert policy.decide(0.99, 0.94) == Decision.STAY_SHALLOW
    assert policy.decide(0.96, 0.96) == Decision.TRIGGER_DEEP
