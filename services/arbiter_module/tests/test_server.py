import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add generated stubs to sys.path
repo_root = Path(__file__).resolve().parents[3]
gen_dir = repo_root / "libs" / "chronos_common" / "generated"
if str(gen_dir) not in sys.path:
    sys.path.insert(0, str(gen_dir))

import arbiter_pb2
import common_pb2
import system2_verifier_pb2
import grpc
from chronos_common.signing import Ed25519Signer, KeyPair
from src.governance import GovernanceRegistry
from src.posp_consensus import ConsensusEngine
from src.server import MetaArbiterServicer


def _create_servicer(timeout_seconds: float = 5.0):
    engine = ConsensusEngine()
    governance = GovernanceRegistry()
    keypair = KeyPair.generate("arbiter-node")
    signer = Ed25519Signer(keypair)
    servicer = MetaArbiterServicer(engine, governance, signer, "arbiter-node", escalation_timeout_seconds=timeout_seconds)
    return servicer, engine


class MockContext:
    def __init__(self):
        self.code = None
        self.details = None

    def abort(self, code, details):
        self.code = code
        self.details = details
        raise grpc.RpcError(f"RPC aborted with {code}: {details}")


def test_submit_sample_valid_signature():
    servicer, engine = _create_servicer()
    engine.open_round("round-1", "cand-1", contested_grounded=True, escalation_reason="test")

    arbiter_keypair = KeyPair.generate("node-1")
    signer = Ed25519Signer(arbiter_keypair)
    payload = {
        "round_id": "round-1",
        "arbiter_node_id": "node-1",
        "vote_grounded": True,
        "stake_collateral": 10.0,
    }
    signed = signer.sign(payload)

    sample_request = arbiter_pb2.ConsensusSample(
        round_id="round-1",
        arbiter_node_id="node-1",
        vote_grounded=True,
        stake_collateral=10.0,
        signature=common_pb2.Signature(
            signer_id=signed.signer_id,
            public_key=signed.public_key,
            signature=signed.signature,
        ),
    )

    ctx = MockContext()
    ack = servicer.SubmitSample(sample_request, ctx)
    assert ack.accepted is True
    assert ack.round_id == "round-1"


def test_submit_sample_invalid_signature():
    servicer, engine = _create_servicer()
    engine.open_round("round-1", "cand-1", contested_grounded=True, escalation_reason="test")

    arbiter_keypair = KeyPair.generate("node-1")
    signer = Ed25519Signer(arbiter_keypair)
    payload = {
        "round_id": "round-1",
        "arbiter_node_id": "node-1",
        "vote_grounded": True,
        "stake_collateral": 10.0,
    }
    signed = signer.sign(payload)

    bad_sig = bytearray(signed.signature)
    bad_sig[0] ^= 0xFF

    sample_request = arbiter_pb2.ConsensusSample(
        round_id="round-1",
        arbiter_node_id="node-1",
        vote_grounded=True,
        stake_collateral=10.0,
        signature=common_pb2.Signature(
            signer_id=signed.signer_id,
            public_key=signed.public_key,
            signature=bytes(bad_sig),
        ),
    )

    ctx = MockContext()
    with pytest.raises(grpc.RpcError):
        servicer.SubmitSample(sample_request, ctx)

    assert ctx.code == grpc.StatusCode.INVALID_ARGUMENT
    assert "invalid sample signature" in ctx.details


def test_submit_sample_missing_signature():
    servicer, engine = _create_servicer()
    engine.open_round("round-1", "cand-1", contested_grounded=True, escalation_reason="test")

    sample_request = arbiter_pb2.ConsensusSample(
        round_id="round-1",
        arbiter_node_id="node-1",
        vote_grounded=True,
        stake_collateral=10.0,
    )

    ctx = MockContext()
    with pytest.raises(grpc.RpcError):
        servicer.SubmitSample(sample_request, ctx)

    assert ctx.code == grpc.StatusCode.INVALID_ARGUMENT
    assert "sample signature is required" in ctx.details


def test_submit_sample_mismatched_signer_id():
    servicer, engine = _create_servicer()
    engine.open_round("round-1", "cand-1", contested_grounded=True, escalation_reason="test")

    attacker_keypair = KeyPair.generate("attacker-node")
    signer = Ed25519Signer(attacker_keypair)
    payload = {
        "round_id": "round-1",
        "arbiter_node_id": "victim-node",
        "vote_grounded": True,
        "stake_collateral": 10.0,
    }
    signed = signer.sign(payload)

    sample_request = arbiter_pb2.ConsensusSample(
        round_id="round-1",
        arbiter_node_id="victim-node",
        vote_grounded=True,
        stake_collateral=10.0,
        signature=common_pb2.Signature(
            signer_id="attacker-node",
            public_key=signed.public_key,
            signature=signed.signature,
        ),
    )

    ctx = MockContext()
    with pytest.raises(grpc.RpcError):
        servicer.SubmitSample(sample_request, ctx)

    assert ctx.code == grpc.StatusCode.INVALID_ARGUMENT
    assert "signature signer_id does not match arbiter_node_id" in ctx.details


def test_escalate_valid_signature():
    servicer, _ = _create_servicer(timeout_seconds=0.01)

    verifier_keypair = KeyPair.generate("verifier-node")
    signer = Ed25519Signer(verifier_keypair)
    payload = {
        "candidate_id": "cand-123",
        "verdict": "ESCALATED",
        "huber_residual": 1.2,
        "rationale": "High Feeling-of-Conflict",
    }
    signed = signer.sign(payload)

    contested = system2_verifier_pb2.VerificationResult(
        candidate_id="cand-123",
        verdict=system2_verifier_pb2.VERIFICATION_VERDICT_ESCALATED,
        huber_residual=1.2,
        rationale="High Feeling-of-Conflict",
        verifier_signature=common_pb2.Signature(
            signer_id=signed.signer_id,
            public_key=signed.public_key,
            signature=signed.signature,
        ),
    )

    request = arbiter_pb2.EscalationRequest(
        contested_result=contested,
        escalation_reason="high conflict",
    )

    ctx = MockContext()
    decision = servicer.Escalate(request, ctx)
    assert decision.round_id is not None
    assert decision.outcome == arbiter_pb2.ARBITRATION_OUTCOME_DEADLOCKED


def test_escalate_invalid_signature():
    servicer, _ = _create_servicer(timeout_seconds=0.01)

    verifier_keypair = KeyPair.generate("verifier-node")
    signer = Ed25519Signer(verifier_keypair)
    payload = {
        "candidate_id": "cand-123",
        "verdict": "ESCALATED",
        "huber_residual": 1.2,
        "rationale": "High Feeling-of-Conflict",
    }
    signed = signer.sign(payload)

    bad_sig = bytearray(signed.signature)
    bad_sig[0] ^= 0xFF

    contested = system2_verifier_pb2.VerificationResult(
        candidate_id="cand-123",
        verdict=system2_verifier_pb2.VERIFICATION_VERDICT_ESCALATED,
        huber_residual=1.2,
        rationale="High Feeling-of-Conflict",
        verifier_signature=common_pb2.Signature(
            signer_id=signed.signer_id,
            public_key=signed.public_key,
            signature=bytes(bad_sig),
        ),
    )

    request = arbiter_pb2.EscalationRequest(
        contested_result=contested,
        escalation_reason="high conflict",
    )

    ctx = MockContext()
    with pytest.raises(grpc.RpcError):
        servicer.Escalate(request, ctx)

    assert ctx.code == grpc.StatusCode.INVALID_ARGUMENT
    assert "invalid verifier signature on contested_result" in ctx.details


def test_escalate_missing_signature():
    servicer, _ = _create_servicer(timeout_seconds=0.01)

    contested = system2_verifier_pb2.VerificationResult(
        candidate_id="cand-123",
        verdict=system2_verifier_pb2.VERIFICATION_VERDICT_ESCALATED,
        huber_residual=1.2,
        rationale="High Feeling-of-Conflict",
    )

    request = arbiter_pb2.EscalationRequest(
        contested_result=contested,
        escalation_reason="high conflict",
    )

    ctx = MockContext()
    with pytest.raises(grpc.RpcError):
        servicer.Escalate(request, ctx)

    assert ctx.code == grpc.StatusCode.INVALID_ARGUMENT
    assert "contested_result verifier signature is required" in ctx.details


def test_get_governance_action_valid_subject():
    servicer, _ = _create_servicer()
    req = arbiter_pb2.GovernanceQuery(subject_id="node-123")
    ctx = MockContext()
    action = servicer.GetGovernanceAction(req, ctx)
    assert action.subject_id == "node-123"


def test_get_governance_action_empty_subject():
    servicer, _ = _create_servicer()
    req = arbiter_pb2.GovernanceQuery(subject_id="")
    ctx = MockContext()
    with pytest.raises(grpc.RpcError):
        servicer.GetGovernanceAction(req, ctx)

    assert ctx.code == grpc.StatusCode.INVALID_ARGUMENT
    assert "subject_id must be non-empty" in ctx.details


def test_get_governance_action_whitespace_subject():
    servicer, _ = _create_servicer()
    req = arbiter_pb2.GovernanceQuery(subject_id="   ")
    ctx = MockContext()
    with pytest.raises(grpc.RpcError):
        servicer.GetGovernanceAction(req, ctx)

    assert ctx.code == grpc.StatusCode.INVALID_ARGUMENT
    assert "subject_id must be non-empty" in ctx.details
