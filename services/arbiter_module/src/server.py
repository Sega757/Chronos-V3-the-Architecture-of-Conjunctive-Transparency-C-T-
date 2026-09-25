"""gRPC server for System 0 (MetaArbiter).

INTERFACE BOUNDARY: this is the only service permitted to issue an
ArbitrationDecision or slash an arbiter node's stake. Escalate() blocks
(up to a bounded timeout) waiting for enough SubmitSample calls from
other arbiter-node processes to reach quorum, then resolves the round via
ConsensusEngine and returns a signed decision.
"""

from __future__ import annotations

import logging
import os
import uuid
from concurrent import futures

import grpc

from chronos_common.signing import Ed25519Signer, KeyPair

from src.exceptions import DuplicateSampleError, InvalidRequestError, SigningError, UnknownRoundError
from src.governance import GovernanceRegistry
from src.posp_consensus import ConsensusEngine, Outcome, Sample

try:
    # protoc emits flat, non-package-relative imports between generated
    # files, so these are imported as top-level modules -- the generated/
    # directory is added directly to PYTHONPATH (see Dockerfile / Makefile),
    # not as a dotted `chronos_common.generated` subpackage.
    import common_pb2
    import arbiter_pb2
    import arbiter_pb2_grpc
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "gRPC stubs are not generated. Run `make proto` from the repo root "
        "before starting this service."
    ) from exc

logger = logging.getLogger("arbiter.server")

_OUTCOME_TO_PROTO = {
    Outcome.UPHELD: arbiter_pb2.ARBITRATION_OUTCOME_UPHELD,
    Outcome.OVERTURNED: arbiter_pb2.ARBITRATION_OUTCOME_OVERTURNED,
    Outcome.DEADLOCKED: arbiter_pb2.ARBITRATION_OUTCOME_DEADLOCKED,
}


class MetaArbiterServicer(arbiter_pb2_grpc.MetaArbiterServicer):
    def __init__(
        self,
        engine: ConsensusEngine,
        governance: GovernanceRegistry,
        signer: Ed25519Signer,
        node_id: str,
        escalation_timeout_seconds: float = 5.0,
    ) -> None:
        self._engine = engine
        self._governance = governance
        self._signer = signer
        self._node_id = node_id
        self._escalation_timeout_seconds = escalation_timeout_seconds

    def Escalate(self, request, context):
        contested = request.contested_result
        if not contested.candidate_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "contested_result.candidate_id must be set")

        round_id = str(uuid.uuid4())
        contested_grounded = contested.verdict == 1  # VERIFICATION_VERDICT_GROUNDED == 1 (see system2_verifier.proto)
        self._engine.open_round(
            round_id=round_id,
            candidate_id=contested.candidate_id,
            contested_grounded=contested_grounded,
            escalation_reason=request.escalation_reason,
        )

        round_ = self._engine.await_resolution(round_id, timeout_seconds=self._escalation_timeout_seconds)

        for slashed_id in round_.slashed_node_ids:
            self._governance.record_slash(slashed_id, round_id, fraction=0.10)

        try:
            signed = self._signer.sign(
                {
                    "round_id": round_id,
                    "outcome": round_.outcome.value,
                    "nash_equilibrium_score": round_.nash_equilibrium_score,
                    "slashed_node_ids": sorted(round_.slashed_node_ids),
                }
            )
        except Exception as exc:  # noqa: BLE001
            context.abort(grpc.StatusCode.INTERNAL, f"failed to sign decision for round {round_id}: {exc}")
            return

        return arbiter_pb2.ArbitrationDecision(
            round_id=round_id,
            outcome=_OUTCOME_TO_PROTO[round_.outcome],
            nash_equilibrium_score=round_.nash_equilibrium_score or 0.0,
            slashed_node_ids=round_.slashed_node_ids,
            decision_merkle_hash=common_pb2.ContentHash(algorithm="SHA-256", digest=signed.payload_hash),
        )

    def SubmitSample(self, request, context):
        if not request.round_id or not request.arbiter_node_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "round_id and arbiter_node_id are required")
        if request.stake_collateral <= 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "stake_collateral must be > 0")

        try:
            self._engine.submit_sample(
                Sample(
                    arbiter_node_id=request.arbiter_node_id,
                    vote_grounded=request.vote_grounded,
                    stake_collateral=request.stake_collateral,
                ),
                round_id=request.round_id,
            )
        except UnknownRoundError as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        except DuplicateSampleError as exc:
            context.abort(grpc.StatusCode.ALREADY_EXISTS, str(exc))

        return arbiter_pb2.SampleAck(round_id=request.round_id, accepted=True)

    def GetGovernanceAction(self, request, context):
        if not request.subject_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "subject_id must be set")
        action = self._governance.get(request.subject_id)
        return arbiter_pb2.GovernanceAction(
            subject_id=action.subject_id,
            legitimacy_basis=action.legitimacy_basis,
            efficacy_metric=action.efficacy_metric,
            justification=action.justification,
            distribution_policy=action.distribution_policy,
            accountable_party=action.accountable_party,
            sanction=action.sanction,
        )


def serve() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    node_id = os.environ.get("NODE_ID", "arbiter-local")
    port = os.environ.get("GRPC_PORT", "50053")
    timeout_seconds = float(os.environ.get("ESCALATION_TIMEOUT_SECONDS", "5.0"))

    keypair = KeyPair.generate(node_id)  # NOTE: production must load a persisted key.
    signer = Ed25519Signer(keypair)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
    arbiter_pb2_grpc.add_MetaArbiterServicer_to_server(
        MetaArbiterServicer(ConsensusEngine(), GovernanceRegistry(), signer, node_id, timeout_seconds),
        server,
    )
    server.add_insecure_port(f"[::]:{port}")
    logger.info("System 0 (MetaArbiter) listening on :%s as node_id=%s", port, node_id)
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
