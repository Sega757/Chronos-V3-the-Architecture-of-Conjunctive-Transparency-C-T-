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
import grpc
from chronos_common.signing import Ed25519Signer, KeyPair
from src.governance import GovernanceRegistry
from src.posp_consensus import ConsensusEngine
from src.server import MetaArbiterServicer


def _create_servicer():
    engine = ConsensusEngine()
    governance = GovernanceRegistry()
    keypair = KeyPair.generate("arbiter-node")
    signer = Ed25519Signer(keypair)
    servicer = MetaArbiterServicer(engine, governance, signer, "arbiter-node")
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
