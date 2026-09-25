"""The zero-hallucination lock.

This module is the single place that is allowed to decide a
VerificationVerdict. Every other module in System 2 (and every caller)
must go through `decide_verdict` -- there is no other constructor for a
GROUNDED verdict anywhere in this service.

Invariant (see docs/architecture/04-invariants.md#inv-2): GROUNDED is only
reachable when ground_truth_refs is non-empty AND the Huber residual is
within tolerance AND the candidate's own Feeling-of-Conflict is below the
escalation threshold. Any other combination yields REJECTED or ESCALATED.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Verdict(str, Enum):
    GROUNDED = "GROUNDED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"


# Tuning constants. Kept as module-level constants (rather than buried
# magic numbers in the decision function) so they are visible to auditors
# and to callers that log/report on why a verdict was reached.
HUBER_RESIDUAL_GROUNDED_MAX = 1.5
FEELING_OF_CONFLICT_ESCALATION_THRESHOLD = 0.6


@dataclass(frozen=True)
class VerdictDecision:
    verdict: Verdict
    rationale: str


def decide_verdict(
    *,
    has_ground_truth_refs: bool,
    huber_residual: float | None,
    feeling_of_conflict: float,
) -> VerdictDecision:
    if not has_ground_truth_refs:
        return VerdictDecision(
            Verdict.REJECTED,
            "zero-hallucination lock: no ground_truth_refs supplied, so no GROUNDED "
            "verdict is reachable regardless of the candidate's own confidence.",
        )

    if huber_residual is None:
        return VerdictDecision(
            Verdict.REJECTED,
            "zero-hallucination lock: ground truth could not be resolved into a "
            "residual; failing closed.",
        )

    if feeling_of_conflict >= FEELING_OF_CONFLICT_ESCALATION_THRESHOLD:
        return VerdictDecision(
            Verdict.ESCALATED,
            f"feeling_of_conflict={feeling_of_conflict:.3f} >= "
            f"{FEELING_OF_CONFLICT_ESCALATION_THRESHOLD}: routing to System 0 "
            "(Meta-Arbiter) for PoSP consensus rather than deciding unilaterally.",
        )

    if huber_residual <= HUBER_RESIDUAL_GROUNDED_MAX:
        return VerdictDecision(
            Verdict.GROUNDED,
            f"huber_residual={huber_residual:.4f} <= {HUBER_RESIDUAL_GROUNDED_MAX} "
            "against the robust ALS-IRLS ground-truth estimate; grounded.",
        )

    return VerdictDecision(
        Verdict.REJECTED,
        f"huber_residual={huber_residual:.4f} exceeds tolerance "
        f"({HUBER_RESIDUAL_GROUNDED_MAX}); candidate contradicts ground truth.",
    )
