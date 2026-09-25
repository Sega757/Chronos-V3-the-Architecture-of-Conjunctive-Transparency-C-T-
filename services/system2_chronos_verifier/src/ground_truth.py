"""Access to the verified knowledge store.

`GroundTruthStore` is the seam where a real knowledge base, vector store,
or curated fact database plugs in. `InMemoryGroundTruthStore` is a
deterministic stand-in for local development and tests: it derives a
stable embedding for each ref from its own text so unit tests do not need
network or database access.
"""

from __future__ import annotations

import hashlib
from typing import Protocol

import numpy as np

from src.exceptions import GroundTruthUnavailableError

EMBEDDING_DIM = 16


class GroundTruthStore(Protocol):
    def resolve(self, refs: list[str]) -> list[np.ndarray]:
        """Return one embedding per ref, in order. Raises
        GroundTruthUnavailableError if any ref cannot be resolved."""
        ...


class InMemoryGroundTruthStore:
    def __init__(self, known_refs: dict[str, np.ndarray] | None = None) -> None:
        self._known_refs = known_refs or {}

    def register(self, ref: str, embedding: np.ndarray) -> None:
        self._known_refs[ref] = embedding

    def resolve(self, refs: list[str]) -> list[np.ndarray]:
        if not refs:
            raise GroundTruthUnavailableError("no ground_truth_refs supplied")
        out: list[np.ndarray] = []
        for ref in refs:
            if ref in self._known_refs:
                out.append(self._known_refs[ref])
                continue
            # Deterministic stand-in embedding, derived from the ref text
            # itself -- NOT a substitute for a real knowledge store. This
            # only exists so the pipeline is runnable without external
            # infrastructure during development.
            seed = int.from_bytes(hashlib.sha256(ref.encode("utf-8")).digest()[:8], "big")
            rng = np.random.default_rng(seed)
            out.append(rng.normal(size=EMBEDDING_DIM))
        return out
