from src.zero_hallucination import (
    FEELING_OF_CONFLICT_ESCALATION_THRESHOLD,
    HUBER_RESIDUAL_GROUNDED_MAX,
    Verdict,
    decide_verdict,
)


def test_no_ground_truth_refs_never_grounds():
    decision = decide_verdict(has_ground_truth_refs=False, huber_residual=0.0, feeling_of_conflict=0.0)
    assert decision.verdict == Verdict.REJECTED


def test_missing_residual_fails_closed():
    decision = decide_verdict(has_ground_truth_refs=True, huber_residual=None, feeling_of_conflict=0.0)
    assert decision.verdict == Verdict.REJECTED


def test_high_conflict_escalates_even_with_good_residual():
    decision = decide_verdict(
        has_ground_truth_refs=True,
        huber_residual=0.0,
        feeling_of_conflict=FEELING_OF_CONFLICT_ESCALATION_THRESHOLD,
    )
    assert decision.verdict == Verdict.ESCALATED


def test_low_residual_low_conflict_grounds():
    decision = decide_verdict(
        has_ground_truth_refs=True,
        huber_residual=HUBER_RESIDUAL_GROUNDED_MAX - 0.01,
        feeling_of_conflict=0.0,
    )
    assert decision.verdict == Verdict.GROUNDED


def test_high_residual_rejects():
    decision = decide_verdict(
        has_ground_truth_refs=True,
        huber_residual=HUBER_RESIDUAL_GROUNDED_MAX + 1.0,
        feeling_of_conflict=0.0,
    )
    assert decision.verdict == Verdict.REJECTED
