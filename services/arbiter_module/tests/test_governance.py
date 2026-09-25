from src.governance import GovernanceAction, GovernanceRegistry


def test_unknown_subject_returns_default_record():
    registry = GovernanceRegistry()
    action = registry.get("some-node")
    assert action.subject_id == "some-node"
    assert action.sanction == "none recorded"


def test_record_slash_is_reflected_in_subsequent_get():
    registry = GovernanceRegistry()
    registry.record_slash("node-dissent", round_id="r4", fraction=0.1)
    action = registry.get("node-dissent")
    assert "STAKE_SLASH" in action.sanction
    assert "r4" in action.justification


def test_explicit_record_overrides_default():
    registry = GovernanceRegistry()
    custom = GovernanceAction(
        subject_id="policy-x",
        legitimacy_basis="board vote",
        efficacy_metric="uptime",
        justification="approved",
        distribution_policy="global",
        accountable_party="ops-team",
        sanction="none",
    )
    registry.record(custom)
    assert registry.get("policy-x") == custom
