"""gRPC server for System 2 (ChronosVerifier).

INTERFACE BOUNDARY: this is the only service in SCCS permitted to emit a
VerificationResult, and decide_verdict() (zero_hallucination.py) is the
only function permitted to choose a VerificationVerdict. Nothing in this
file bypasses it.
"""

from __future__ import annotations

import logging
import os
from concurrent import futures

import grpc
import numpy as np

from chronos_common.merkle import merkle_root
from chronos_common.signing import Ed25519Signer, KeyPair

from src.exceptions import GroundTruthUnavailableError, InvalidRequestError, SigningError
from src.ground_truth import GroundTruthStore, InMemoryGroundTruthStore
from src.robust_stats import candidate_huber_residual
from src.zero_hallucination import Verdict, decide_verdict

try:
    # protoc emits flat, non-package-relative imports between generated
    # files, so these are imported as top-level modules -- the generated/
    # directory is added directly to PYTHONPATH (see Dockerfile / Makefile),
    # not as a dotted `chronos_common.generated` subpackage.
    import common_pb2
    import system2_verifier_pb2
    import system2_verifier_pb2_grpc
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "gRPC stubs are not generated. Run `make proto` from the repo root "
        "before starting this service."
    ) from exc

logger = logging.getLogger("system2.server")

_VERDICT_TO_PROTO = {
    Verdict.GROUNDED: system2_verifier_pb2.VERIFICATION_VERDICT_GROUNDED,
    Verdict.REJECTED: system2_verifier_pb2.VERIFICATION_VERDICT_REJECTED,
    Verdict.ESCALATED: system2_verifier_pb2.VERIFICATION_VERDICT_ESCALATED,
}


class ChronosVerifierServicer(system2_verifier_pb2_grpc.ChronosVerifierServicer):
    def __init__(self, store: GroundTruthStore, signer: Ed25519Signer, node_id: str) -> None:
        self._store = store
        self._signer = signer
        self._node_id = node_id

    def Verify(self, request, context):
        try:
            result = self._verify_one(request)
        except InvalidRequestError as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except SigningError as exc:
            context.abort(grpc.StatusCode.INTERNAL, str(exc))
        return result

    def BatchVerify(self, request, context):
        if not request.requests:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "at least one VerificationRequest is required")

        results = []
        for req in request.requests:
            try:
                results.append(self._verify_one(req))
            except InvalidRequestError as exc:
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
            except SigningError as exc:
                context.abort(grpc.StatusCode.INTERNAL, str(exc))

        # merkle_leaf_hash.digest is already a SHA-256 leaf hash for each
        # result, so it is used directly as the batch's Merkle leaves.
        leaves = [bytes(r.merkle_leaf_hash.digest) for r in results]
        root = merkle_root(leaves)

        return system2_verifier_pb2.BatchVerificationResult(
            results=results,
            batch_merkle_root=common_pb2.ContentHash(algorithm="SHA-256", digest=root),
        )

    def _verify_one(self, request):
        candidate = request.candidate
        if not candidate.candidate_id:
            raise InvalidRequestError("candidate.candidate_id must be set")

        candidate_embedding = self._extract_embedding(candidate)
        huber_residual = None
        try:
            if request.ground_truth_refs:
                reference_embeddings = self._store.resolve(list(request.ground_truth_refs))
                huber_residual = candidate_huber_residual(candidate_embedding, reference_embeddings)
        except GroundTruthUnavailableError as exc:
            logger.warning("ground truth unavailable for %s: %s", candidate.candidate_id, exc)
            huber_residual = None

        decision = decide_verdict(
            has_ground_truth_refs=bool(request.ground_truth_refs),
            huber_residual=huber_residual,
            feeling_of_conflict=candidate.epistemic_state.feeling_of_conflict,
        )

        payload = {
            "candidate_id": candidate.candidate_id,
            "verdict": decision.verdict.value,
            "huber_residual": huber_residual if huber_residual is not None else -1.0,
            "rationale": decision.rationale,
        }
        try:
            signed = self._signer.sign(payload)
        except Exception as exc:  # noqa: BLE001
            raise SigningError(f"failed to sign verification for {candidate.candidate_id}: {exc}") from exc

        return system2_verifier_pb2.VerificationResult(
            candidate_id=candidate.candidate_id,
            verdict=_VERDICT_TO_PROTO[decision.verdict],
            huber_residual=huber_residual if huber_residual is not None else -1.0,
            rationale=decision.rationale,
            merkle_leaf_hash=common_pb2.ContentHash(algorithm="SHA-256", digest=signed.payload_hash),
            verifier_signature=common_pb2.Signature(
                signer_id=signed.signer_id,
                public_key=signed.public_key,
                signature=signed.signature,
                payload_hash=common_pb2.ContentHash(algorithm="SHA-256", digest=signed.payload_hash),
            ),
        )

    @staticmethod
    def _extract_embedding(candidate) -> np.ndarray:
        """Derive a numeric embedding for the candidate's content.

        Placeholder: a real deployment replaces this with the same
        embedding model used to populate the ground-truth store, so
        candidate and reference vectors live in a comparable space. Kept
        deterministic here so the service is testable without a model
        dependency.
        """
        import hashlib

        seed = int.from_bytes(hashlib.sha256(candidate.content.encode("utf-8")).digest()[:8], "big")
        rng = np.random.default_rng(seed)
        return rng.normal(size=16)


def serve() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    node_id = os.environ.get("NODE_ID", "system2-local")
    port = os.environ.get("GRPC_PORT", "50052")

    keypair = KeyPair.generate(node_id)  # NOTE: production must load a persisted key.
    signer = Ed25519Signer(keypair)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
    system2_verifier_pb2_grpc.add_ChronosVerifierServicer_to_server(
        ChronosVerifierServicer(InMemoryGroundTruthStore(), signer, node_id), server
    )
    server.add_insecure_port(f"[::]:{port}")
    logger.info("System 2 (ChronosVerifier) listening on :%s as node_id=%s", port, node_id)
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
