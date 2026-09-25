"""Proof-of-Sampling (PoSP) consensus among registered arbiter nodes.

Each arbiter node stakes collateral behind its vote on whether a contested
VerificationResult should stand. The round resolves once enough stake has
voted (a quorum) or a timeout elapses. The resolution is treated as a
simple stake-weighted game: each node's payoff is highest when it votes
with the eventual majority, so wide agreement across independently staked
nodes approximates a Nash equilibrium of that game -- the
``nash_equilibrium_score`` reported below is how far the round's outcome
is from a 50/50 split, i.e. how stable that equilibrium is. A round that
never clears the disagreement threshold is DEADLOCKED and escalated to a
human rather than resolved automatically.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum

from src.exceptions import DuplicateSampleError, InvalidRequestError, UnknownRoundError

# A round is considered "decisive" (not deadlocked) once the stake-weighted
# split diverges from 50/50 by at least this much.
DECISIVENESS_THRESHOLD = 0.20

# Fraction of collateral slashed from a node that voted against a decisive
# majority outcome -- the PoSP incentive to vote honestly/carefully.
SLASH_FRACTION = 0.10


class Outcome(str, Enum):
    UPHELD = "UPHELD"
    OVERTURNED = "OVERTURNED"
    DEADLOCKED = "DEADLOCKED"


@dataclass
class Sample:
    arbiter_node_id: str
    vote_grounded: bool
    stake_collateral: float


@dataclass
class ConsensusRound:
    round_id: str
    candidate_id: str
    contested_grounded: bool  # True iff the escalated result claimed GROUNDED
    escalation_reason: str
    quorum_stake: float
    samples: dict[str, Sample] = field(default_factory=dict)
    status: str = "OPEN"
    lock: threading.Lock = field(default_factory=threading.Lock)
    resolved_event: threading.Event = field(default_factory=threading.Event)
    outcome: Outcome | None = None
    nash_equilibrium_score: float | None = None
    slashed_node_ids: list[str] = field(default_factory=list)


class ConsensusEngine:
    def __init__(self, *, default_quorum_stake: float = 3.0, default_timeout_seconds: float = 5.0) -> None:
        self._rounds: dict[str, ConsensusRound] = {}
        self._registry_lock = threading.Lock()
        self._default_quorum_stake = default_quorum_stake
        self._default_timeout_seconds = default_timeout_seconds

    def open_round(self, round_id: str, candidate_id: str, contested_grounded: bool, escalation_reason: str) -> ConsensusRound:
        if not round_id:
            raise InvalidRequestError("round_id must be non-empty")
        round_ = ConsensusRound(
            round_id=round_id,
            candidate_id=candidate_id,
            contested_grounded=contested_grounded,
            escalation_reason=escalation_reason,
            quorum_stake=self._default_quorum_stake,
        )
        with self._registry_lock:
            self._rounds[round_id] = round_
        return round_

    def submit_sample(self, sample: Sample, round_id: str) -> None:
        round_ = self._rounds.get(round_id)
        if round_ is None:
            raise UnknownRoundError(f"no open round with round_id={round_id!r}")
        with round_.lock:
            if round_.status != "OPEN":
                return  # round already resolved; late samples are accepted but ignored for the outcome
            if sample.arbiter_node_id in round_.samples:
                raise DuplicateSampleError(
                    f"node {sample.arbiter_node_id!r} already submitted a sample for round {round_id!r}"
                )
            round_.samples[sample.arbiter_node_id] = sample
            total_stake = sum(s.stake_collateral for s in round_.samples.values())
            if total_stake >= round_.quorum_stake:
                self._resolve_locked(round_)

    def await_resolution(self, round_id: str, timeout_seconds: float | None = None) -> ConsensusRound:
        round_ = self._rounds.get(round_id)
        if round_ is None:
            raise UnknownRoundError(f"no round with round_id={round_id!r}")
        timeout = self._default_timeout_seconds if timeout_seconds is None else timeout_seconds
        deadline = time.monotonic() + timeout
        if not round_.resolved_event.wait(timeout=max(timeout, 0.0)):
            with round_.lock:
                if round_.status == "OPEN":
                    self._resolve_locked(round_)
        return round_

    def _resolve_locked(self, round_: ConsensusRound) -> None:
        """Resolve ``round_`` in place. Caller must hold ``round_.lock``."""
        samples = list(round_.samples.values())
        weighted_yes = sum(s.stake_collateral for s in samples if s.vote_grounded)
        weighted_no = sum(s.stake_collateral for s in samples if not s.vote_grounded)
        total = weighted_yes + weighted_no

        if total <= 0:
            round_.outcome = Outcome.DEADLOCKED
            round_.nash_equilibrium_score = 0.0
        else:
            score = abs(weighted_yes - weighted_no) / total
            round_.nash_equilibrium_score = score
            if score < DECISIVENESS_THRESHOLD:
                round_.outcome = Outcome.DEADLOCKED
            else:
                majority_grounded = weighted_yes > weighted_no
                round_.outcome = (
                    Outcome.UPHELD if majority_grounded == round_.contested_grounded else Outcome.OVERTURNED
                )
                round_.slashed_node_ids = [
                    s.arbiter_node_id for s in samples if s.vote_grounded != majority_grounded
                ]

        round_.status = round_.outcome.value
        round_.resolved_event.set()
