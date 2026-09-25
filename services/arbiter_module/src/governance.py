"""L-E-J-D-A-S governance registry.

Legitimacy, Efficacy, Justification, Distribution, Accountability,
Sanction -- the six fields every governance action in SCCS must record.
This in-memory registry is a reference implementation; a production
deployment backs it with the ``governance_actions`` / ``sanctions`` tables
in db/migrations/002_governance_schema.sql.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GovernanceAction:
    subject_id: str
    legitimacy_basis: str
    efficacy_metric: str
    justification: str
    distribution_policy: str
    accountable_party: str
    sanction: str


_DEFAULT_ACTION_TEMPLATE = GovernanceAction(
    subject_id="",
    legitimacy_basis="default: PoSP quorum among registered arbiter nodes (see proto/arbiter.proto)",
    efficacy_metric="nash_equilibrium_score over the most recent consensus round involving this subject",
    justification="no governance action has been explicitly recorded for this subject yet",
    distribution_policy="applies only to the named subject_id",
    accountable_party="system0-meta-arbiter",
    sanction="none recorded",
)


class GovernanceRegistry:
    def __init__(self) -> None:
        self._actions: dict[str, GovernanceAction] = {}
        self._lock = threading.Lock()

    def record(self, action: GovernanceAction) -> None:
        with self._lock:
            self._actions[action.subject_id] = action

    def record_slash(self, subject_id: str, round_id: str, fraction: float) -> None:
        self.record(
            GovernanceAction(
                subject_id=subject_id,
                legitimacy_basis="PoSP consensus round outcome (System 0)",
                efficacy_metric=f"voted against the resolved majority in round {round_id}",
                justification=(
                    f"stake slashed by {fraction:.0%} for dissenting from a decisive "
                    f"PoSP consensus outcome in round {round_id}"
                ),
                distribution_policy="applies to this arbiter node's staked collateral only",
                accountable_party="system0-meta-arbiter",
                sanction=f"STAKE_SLASH:{fraction:.2f}",
            )
        )

    def get(self, subject_id: str) -> GovernanceAction:
        with self._lock:
            action = self._actions.get(subject_id)
        if action is not None:
            return action
        return GovernanceAction(
            subject_id=subject_id,
            legitimacy_basis=_DEFAULT_ACTION_TEMPLATE.legitimacy_basis,
            efficacy_metric=_DEFAULT_ACTION_TEMPLATE.efficacy_metric,
            justification=_DEFAULT_ACTION_TEMPLATE.justification,
            distribution_policy=_DEFAULT_ACTION_TEMPLATE.distribution_policy,
            accountable_party=_DEFAULT_ACTION_TEMPLATE.accountable_party,
            sanction=_DEFAULT_ACTION_TEMPLATE.sanction,
        )
