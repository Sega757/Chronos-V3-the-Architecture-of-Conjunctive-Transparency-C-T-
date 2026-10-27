import pytest
import sys
from pathlib import Path

# Add generated stubs to sys.path
repo_root = Path(__file__).resolve().parents[3]
gen_dir = repo_root / "libs" / "chronos_common" / "generated"
if str(gen_dir) not in sys.path:
    sys.path.insert(0, str(gen_dir))

import common_pb2
import system1_hypothesis_pb2
import system2_verifier_pb2
from chronos_common.signing import KeyPair, Ed25519Signer
from src.exceptions import InvalidRequestError
from src.ground_truth import InMemoryGroundTruthStore
from src.server import ChronosVerifierServicer


def _create_signed_candidate(keypair, candidate_id="cand-1", content="test hypothesis content"):
    signer = Ed25519Signer(keypair)
    payload = {
        "candidate_id": candidate_id,
        "content": content,
        "epistemic_state": {
            "shannon_entropy_bits": 0.5,
            "dcu_kappa": 10.0,
            "feeling_of_rightness": 0.9,
            "feeling_of_error": 0.1,
            "feeling_of_conflict": 0.05,
        },
    }
    signed = signer.sign(payload)

    candidate = system1_hypothesis_pb2.HypothesisCandidate(
        candidate_id=candidate_id,
        content=content,
        epistemic_state=common_pb2.EpistemicState(
            shannon_entropy_bits=0.5,
            dcu_kappa=10.0,
            feeling_of_rightness=0.9,
            feeling_of_error=0.1,
            feeling_of_conflict=0.05,
        ),
        provenance=common_pb2.Provenance(
            origin_node_id=keypair.node_id,
            signatures=[
                common_pb2.Signature(
                    signer_id=signed.signer_id,
                    public_key=signed.public_key,
                    signature=signed.signature,
                )
            ],
        ),
    )
    return candidate


def test_verify_one_valid_signature():
    keypair = KeyPair.generate("system1-node")
    verifier_keypair = KeyPair.generate("system2-node")
    store = InMemoryGroundTruthStore()

    candidate = _create_signed_candidate(keypair)
    # Register candidate embedding as ground truth reference so huber residual is 0
    embedding = ChronosVerifierServicer._extract_embedding(candidate)
    store.register("ref-1", embedding)

    servicer = ChronosVerifierServicer(
        store=store,
        signer=Ed25519Signer(verifier_keypair),
        node_id="system2-node",
    )

    request = system2_verifier_pb2.VerificationRequest(
        candidate=candidate,
        ground_truth_refs=["ref-1"],
    )

    result = servicer._verify_one(request)
    assert result.candidate_id == "cand-1"
    assert result.verdict == system2_verifier_pb2.VERIFICATION_VERDICT_GROUNDED


def test_verify_one_invalid_signature():
    keypair = KeyPair.generate("system1-node")
    verifier_keypair = KeyPair.generate("system2-node")
    servicer = ChronosVerifierServicer(
        store=InMemoryGroundTruthStore(),
        signer=Ed25519Signer(verifier_keypair),
        node_id="system2-node",
    )

    candidate = _create_signed_candidate(keypair)
    # Corrupt the signature bytes to simulate tampering / forgery
    bad_sig = bytearray(candidate.provenance.signatures[0].signature)
    bad_sig[0] ^= 0xFF
    candidate.provenance.signatures[0].signature = bytes(bad_sig)

    request = system2_verifier_pb2.VerificationRequest(
        candidate=candidate,
        ground_truth_refs=["ref-1"],
    )

    with pytest.raises(InvalidRequestError, match="invalid candidate signature"):
        servicer._verify_one(request)


def test_verify_one_tampered_content():
    keypair = KeyPair.generate("system1-node")
    verifier_keypair = KeyPair.generate("system2-node")
    servicer = ChronosVerifierServicer(
        store=InMemoryGroundTruthStore(),
        signer=Ed25519Signer(verifier_keypair),
        node_id="system2-node",
    )

    candidate = _create_signed_candidate(keypair, content="original content")
    # Tamper with the content after signing
    candidate.content = "tampered content"

    request = system2_verifier_pb2.VerificationRequest(
        candidate=candidate,
        ground_truth_refs=["ref-1"],
    )

    with pytest.raises(InvalidRequestError, match="invalid candidate signature"):
        servicer._verify_one(request)


def test_verify_one_unsigned_candidate():
    verifier_keypair = KeyPair.generate("system2-node")
    servicer = ChronosVerifierServicer(
        store=InMemoryGroundTruthStore(),
        signer=Ed25519Signer(verifier_keypair),
        node_id="system2-node",
    )

    candidate = system1_hypothesis_pb2.HypothesisCandidate(
        candidate_id="unsigned-1",
        content="unsigned content",
        epistemic_state=common_pb2.EpistemicState(feeling_of_conflict=0.0),
    )
    request = system2_verifier_pb2.VerificationRequest(
        candidate=candidate,
        ground_truth_refs=["ref-1"],
    )

    with pytest.raises(InvalidRequestError, match="candidate signature is required"):
        servicer._verify_one(request)


def test_verify_one_mismatched_signer_id():
    keypair = KeyPair.generate("attacker-node")
    verifier_keypair = KeyPair.generate("system2-node")
    servicer = ChronosVerifierServicer(
        store=InMemoryGroundTruthStore(),
        signer=Ed25519Signer(verifier_keypair),
        node_id="system2-node",
    )

    candidate = _create_signed_candidate(keypair, candidate_id="cand-spoofed")
    # Spoof origin_node_id to simulate an attacker trying to impersonate a legitimate node
    candidate.provenance.origin_node_id = "legitimate-node"

    request = system2_verifier_pb2.VerificationRequest(
        candidate=candidate,
        ground_truth_refs=["ref-1"],
    )

    with pytest.raises(InvalidRequestError, match="signature signer_id does not match origin_node_id"):
        servicer._verify_one(request)


def test_verify_one_empty_signer_id():
    keypair = KeyPair.generate("attacker-node")
    verifier_keypair = KeyPair.generate("system2-node")
    servicer = ChronosVerifierServicer(
        store=InMemoryGroundTruthStore(),
        signer=Ed25519Signer(verifier_keypair),
        node_id="system2-node",
    )

    candidate = _create_signed_candidate(keypair, candidate_id="cand-empty-signer")
    candidate.provenance.origin_node_id = "legitimate-node"
    candidate.provenance.signatures[0].signer_id = ""

    request = system2_verifier_pb2.VerificationRequest(
        candidate=candidate,
        ground_truth_refs=["ref-1"],
    )

    with pytest.raises(InvalidRequestError, match="signature signer_id does not match origin_node_id"):
        servicer._verify_one(request)


def test_batch_verify_invalid_signature():
    keypair = KeyPair.generate("system1-node")
    verifier_keypair = KeyPair.generate("system2-node")
    servicer = ChronosVerifierServicer(
        store=InMemoryGroundTruthStore(),
        signer=Ed25519Signer(verifier_keypair),
        node_id="system2-node",
    )

    candidate1 = _create_signed_candidate(keypair, candidate_id="cand-1")
    candidate2 = _create_signed_candidate(keypair, candidate_id="cand-2")

    # Corrupt signature on candidate2
    bad_sig = bytearray(candidate2.provenance.signatures[0].signature)
    bad_sig[0] ^= 0xFF
    candidate2.provenance.signatures[0].signature = bytes(bad_sig)

    batch_request = system2_verifier_pb2.BatchVerificationRequest(
        requests=[
            system2_verifier_pb2.VerificationRequest(candidate=candidate1),
            system2_verifier_pb2.VerificationRequest(candidate=candidate2),
        ]
    )

    # Simulated context for BatchVerify
    class MockContext:
        def abort(self, code, details):
            raise InvalidRequestError(details)

    with pytest.raises(InvalidRequestError, match="invalid candidate signature"):
        servicer.BatchVerify(batch_request, MockContext())


def test_batch_verify_exceeds_max_batch_size():
    keypair = KeyPair.generate("system1-node")
    verifier_keypair = KeyPair.generate("system2-node")
    servicer = ChronosVerifierServicer(
        store=InMemoryGroundTruthStore(),
        signer=Ed25519Signer(verifier_keypair),
        node_id="system2-node",
    )

    candidate = _create_signed_candidate(keypair, candidate_id="cand-1")
    requests = [system2_verifier_pb2.VerificationRequest(candidate=candidate)] * 129

    batch_request = system2_verifier_pb2.BatchVerificationRequest(requests=requests)

    class MockContext:
        def abort(self, code, details):
            raise InvalidRequestError(details)

    with pytest.raises(InvalidRequestError, match="batch size exceeds maximum limit of 128"):
        servicer.BatchVerify(batch_request, MockContext())
