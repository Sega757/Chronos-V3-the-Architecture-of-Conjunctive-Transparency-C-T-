from src.posp_consensus import ConsensusEngine, Outcome, Sample


def _engine(quorum: float = 3.0) -> ConsensusEngine:
    return ConsensusEngine(default_quorum_stake=quorum, default_timeout_seconds=1.0)


def test_decisive_majority_upholds_when_contested_verdict_matches():
    engine = _engine()
    engine.open_round("r1", "cand-1", contested_grounded=True, escalation_reason="test")
    engine.submit_sample(Sample("node-a", vote_grounded=True, stake_collateral=2.0), "r1")
    engine.submit_sample(Sample("node-b", vote_grounded=True, stake_collateral=1.5), "r1")
    round_ = engine.await_resolution("r1")
    assert round_.outcome == Outcome.UPHELD
    assert round_.slashed_node_ids == []


def test_decisive_majority_overturns_when_it_disagrees():
    engine = _engine()
    engine.open_round("r2", "cand-2", contested_grounded=True, escalation_reason="test")
    engine.submit_sample(Sample("node-a", vote_grounded=False, stake_collateral=2.0), "r2")
    engine.submit_sample(Sample("node-b", vote_grounded=False, stake_collateral=1.5), "r2")
    round_ = engine.await_resolution("r2")
    assert round_.outcome == Outcome.OVERTURNED


def test_close_split_is_deadlocked_and_nobody_is_slashed():
    engine = _engine()
    engine.open_round("r3", "cand-3", contested_grounded=True, escalation_reason="test")
    engine.submit_sample(Sample("node-a", vote_grounded=True, stake_collateral=1.55), "r3")
    engine.submit_sample(Sample("node-b", vote_grounded=False, stake_collateral=1.45), "r3")
    round_ = engine.await_resolution("r3")
    assert round_.outcome == Outcome.DEADLOCKED
    assert round_.slashed_node_ids == []


def test_dissenting_minority_is_slashed_on_decisive_outcome():
    # Quorum is set above the majority node's stake alone (3.0) so the
    # round only resolves once both samples are in -- otherwise it would
    # resolve on the first sample and silently ignore the second.
    engine = _engine(quorum=3.2)
    engine.open_round("r4", "cand-4", contested_grounded=True, escalation_reason="test")
    engine.submit_sample(Sample("node-majority", vote_grounded=True, stake_collateral=3.0), "r4")
    engine.submit_sample(Sample("node-dissent", vote_grounded=False, stake_collateral=0.5), "r4")
    round_ = engine.await_resolution("r4")
    assert round_.outcome == Outcome.UPHELD
    assert round_.slashed_node_ids == ["node-dissent"]


def test_no_samples_before_timeout_is_deadlocked():
    engine = _engine(quorum=100.0)
    engine.open_round("r5", "cand-5", contested_grounded=True, escalation_reason="test")
    round_ = engine.await_resolution("r5", timeout_seconds=0.05)
    assert round_.outcome == Outcome.DEADLOCKED
