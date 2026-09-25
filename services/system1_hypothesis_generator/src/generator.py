"""The stochastic hypothesis generation backend.

`HypothesisModel` is the seam where a real model (an LLM, a retrieval
ensemble, whatever System 1 actually wants to be) plugs in. The
`DeterministicStubModel` shipped here produces reproducible, seeded
candidates so the service is runnable and testable end-to-end without a
model dependency; it is not intended for production use.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from src.exceptions import GenerationBackendError

EMBEDDING_DIM = 16


@dataclass(frozen=True)
class RawCandidate:
    content: str
    probability: float          # this candidate's mass in the sampling distribution
    embedding: np.ndarray        # (EMBEDDING_DIM,) unit-norm-able feature vector
    supporting_features: dict


class HypothesisModel(Protocol):
    def sample(self, query: str, max_candidates: int, temperature: float) -> list[RawCandidate]:
        ...


class DeterministicStubModel:
    """Seeds on the query text so the same query always yields the same
    candidate set -- useful for tests and for demonstrating the pipeline
    without a real generative backend attached."""

    def sample(self, query: str, max_candidates: int, temperature: float) -> list[RawCandidate]:
        if not query.strip():
            raise GenerationBackendError("query must be non-empty")

        seed = int.from_bytes(hashlib.sha256(query.encode("utf-8")).digest()[:8], "big")
        rng = np.random.default_rng(seed)

        raw_weights = rng.dirichlet(alpha=np.full(max_candidates, max(temperature, 1e-3)))
        candidates: list[RawCandidate] = []
        for i, weight in enumerate(raw_weights):
            embedding = rng.normal(size=EMBEDDING_DIM)
            candidates.append(
                RawCandidate(
                    content=f"{query} :: candidate-{i}",
                    probability=float(weight),
                    embedding=embedding,
                    supporting_features={"stub_index": i, "seed": seed},
                )
            )
        return candidates
