"""gRPC server for System 1 (HypothesisGenerator).

INTERFACE BOUNDARY: this server exposes exactly the RPCs declared in
proto/system1_hypothesis.proto. It never accepts a connection from, or
returns data to, anything other than System 2 -- there is no user-facing
listener here, and no code path that skips signing a candidate before it
leaves this process.
"""

from __future__ import annotations

import logging
import os
import uuid
from concurrent import futures
from datetime import datetime, timezone

import grpc

from chronos_common import EpistemicState as EpistemicMath
from chronos_common.epistemics import shannon_entropy, vmf_concentration
from chronos_common.signing import Ed25519Signer, KeyPair

from src.exceptions import GenerationBackendError, InvalidRequestError, SigningError
from src.generator import DeterministicStubModel, HypothesisModel

try:
    # protoc emits flat, non-package-relative imports between generated
    # files, so these are imported as top-level modules -- the generated/
    # directory is added directly to PYTHONPATH (see Dockerfile / Makefile),
    # not as a dotted `chronos_common.generated` subpackage.
    import common_pb2
    import system1_hypothesis_pb2
    import system1_hypothesis_pb2_grpc
except ImportError as exc:  # pragma: no cover - guidance for operators
    raise RuntimeError(
        "gRPC stubs are not generated. Run `make proto` from the repo root "
        "before starting this service."
    ) from exc

logger = logging.getLogger("system1.server")

MAX_CANDIDATES_HARD_LIMIT = 64


class HypothesisGeneratorServicer(system1_hypothesis_pb2_grpc.HypothesisGeneratorServicer):
    def __init__(self, model: HypothesisModel, signer: Ed25519Signer, node_id: str) -> None:
        self._model = model
        self._signer = signer
        self._node_id = node_id

    def GenerateHypotheses(self, request, context):
        try:
            candidates = self._build_candidates(request)
        except InvalidRequestError as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except GenerationBackendError as exc:
            context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))
        except SigningError as exc:
            context.abort(grpc.StatusCode.INTERNAL, str(exc))
        return system1_hypothesis_pb2.HypothesisResponse(
            candidates=candidates,
            batch_id=str(uuid.uuid4()),
        )

    def StreamHypotheses(self, request, context):
        try:
            candidates = self._build_candidates(request)
        except InvalidRequestError as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
            return
        except GenerationBackendError as exc:
            context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))
            return
        except SigningError as exc:
            context.abort(grpc.StatusCode.INTERNAL, str(exc))
            return
        for candidate in candidates:
            yield candidate

    def _build_candidates(self, request) -> list:
        if not request.query.strip():
            raise InvalidRequestError("query must be non-empty")
        max_candidates = request.max_candidates or 8
        if not (0 < max_candidates <= MAX_CANDIDATES_HARD_LIMIT):
            raise InvalidRequestError(
                f"max_candidates must be in (0, {MAX_CANDIDATES_HARD_LIMIT}]"
            )
        temperature = request.temperature or 1.0
        if not (0.0 < temperature <= 2.0):
            raise InvalidRequestError("temperature must be in (0, 2]")

        try:
            raw_candidates = self._model.sample(request.query, max_candidates, temperature)
        except GenerationBackendError:
            raise
        except Exception as exc:  # noqa: BLE001 - backend is untrusted, never let it crash the server
            raise GenerationBackendError(f"generation backend failed: {exc}") from exc

        probabilities = [c.probability for c in raw_candidates]
        max_expected_entropy = shannon_entropy([1.0] * len(raw_candidates)) if raw_candidates else 1.0

        results = []
        for i, raw in enumerate(raw_candidates):
            state = EpistemicMath.derive(
                candidate_probabilities=probabilities,
                candidate_embeddings=raw.embedding.reshape(1, -1),
                max_expected_entropy_bits=max(max_expected_entropy, 1e-6),
            )
            candidate_id = f"{request.query[:16]}-{i}-{uuid.uuid4().hex[:8]}"

            payload = {
                "candidate_id": candidate_id,
                "content": raw.content,
                "epistemic_state": {
                    "shannon_entropy_bits": state.shannon_entropy_bits,
                    "dcu_kappa": state.dcu_kappa,
                    "feeling_of_rightness": state.feeling_of_rightness,
                    "feeling_of_error": state.feeling_of_error,
                    "feeling_of_conflict": state.feeling_of_conflict,
                },
            }
            try:
                signed = self._signer.sign(payload)
            except Exception as exc:  # noqa: BLE001
                raise SigningError(f"failed to sign candidate {candidate_id}: {exc}") from exc

            provenance = common_pb2.Provenance(
                trace_id=request.provenance.trace_id or str(uuid.uuid4()),
                origin_node_id=self._node_id,
                content_hash=common_pb2.ContentHash(algorithm="SHA-256", digest=signed.payload_hash),
                signatures=[
                    common_pb2.Signature(
                        signer_id=signed.signer_id,
                        public_key=signed.public_key,
                        signature=signed.signature,
                        payload_hash=common_pb2.ContentHash(algorithm="SHA-256", digest=signed.payload_hash),
                    )
                ],
            )
            provenance.created_at.FromDatetime(datetime.now(timezone.utc))

            results.append(
                system1_hypothesis_pb2.HypothesisCandidate(
                    candidate_id=candidate_id,
                    content=raw.content,
                    epistemic_state=common_pb2.EpistemicState(
                        shannon_entropy_bits=state.shannon_entropy_bits,
                        dcu_kappa=state.dcu_kappa,
                        feeling_of_rightness=state.feeling_of_rightness,
                        feeling_of_error=state.feeling_of_error,
                        feeling_of_conflict=state.feeling_of_conflict,
                        primary_basis=common_pb2.CONFIDENCE_BASIS_DIRECTIONAL_CONSISTENCY,
                    ),
                    provenance=provenance,
                )
            )
        return results


def serve() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    node_id = os.environ.get("NODE_ID", "system1-local")
    port = os.environ.get("GRPC_PORT", "50051")

    keypair = KeyPair.generate(node_id)  # NOTE: production deployments must load a
    signer = Ed25519Signer(keypair)      # persisted key, not generate one per process start.

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
    system1_hypothesis_pb2_grpc.add_HypothesisGeneratorServicer_to_server(
        HypothesisGeneratorServicer(DeterministicStubModel(), signer, node_id), server
    )
    server.add_insecure_port(f"[::]:{port}")
    logger.info("System 1 (HypothesisGenerator) listening on :%s as node_id=%s", port, node_id)
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
