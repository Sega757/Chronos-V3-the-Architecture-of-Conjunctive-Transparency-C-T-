"""Quantitative epistemic-state primitives shared by System 1 and System 2.

Implements:
  * Shannon entropy H(X) over a discrete candidate distribution.
  * A directional-consistency concentration estimate (von Mises-Fisher
    kappa) over a set of unit-norm embedding vectors, used as the
    Directional Consistency Uncertainty (DCU) signal.
  * FOR / FOE / FOC (Feeling of Rightness / Error / Conflict) derived from
    those two signals.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

_EPS = 1e-12


def shannon_entropy(probabilities: list[float]) -> float:
    """H(X) = -sum(p_i * log2(p_i)), in bits. Zero-probability entries are
    skipped (0 log 0 := 0 by convention)."""
    total = sum(probabilities)
    if total <= 0:
        raise ValueError("shannon_entropy: probabilities must sum to > 0")
    h = 0.0
    for p in probabilities:
        q = p / total
        if q > _EPS:
            h -= q * math.log2(q)
    return h


def vmf_concentration(unit_vectors: np.ndarray) -> float:
    """Estimate the von Mises-Fisher concentration parameter kappa for a
    set of unit-norm vectors on the (p-1)-sphere, using the standard
    approximation from Banerjee et al. (2005):

        R_bar = |sum(x_i)| / n
        kappa ~= R_bar * (p - R_bar^2) / (1 - R_bar^2)

    Higher kappa means the vectors point in a more consistent direction
    (low uncertainty); kappa -> 0 as they approach a uniform spread.
    ``unit_vectors`` is an (n, p) array; rows need not be pre-normalized.
    """
    if unit_vectors.ndim != 2 or unit_vectors.shape[0] == 0:
        raise ValueError("vmf_concentration: expected a non-empty (n, p) array")
    n, p = unit_vectors.shape
    norms = np.linalg.norm(unit_vectors, axis=1, keepdims=True)
    norms = np.where(norms < _EPS, 1.0, norms)
    normalized = unit_vectors / norms
    resultant = normalized.sum(axis=0)
    r_bar = float(np.linalg.norm(resultant) / n)
    r_bar = min(r_bar, 1.0 - 1e-9)
    if r_bar < _EPS:
        return 0.0
    kappa = r_bar * (p - r_bar**2) / (1 - r_bar**2)
    return float(kappa)


@dataclass(frozen=True)
class EpistemicState:
    shannon_entropy_bits: float
    dcu_kappa: float
    feeling_of_rightness: float
    feeling_of_error: float
    feeling_of_conflict: float

    @classmethod
    def derive(
        cls,
        *,
        candidate_probabilities: list[float],
        candidate_embeddings: np.ndarray,
        max_expected_entropy_bits: float,
    ) -> "EpistemicState":
        """Derive an EpistemicState from a candidate distribution and its
        embedding set.

        FOR (rightness) rises with directional consistency (kappa) and
        falls with normalized entropy. FOE (error) is its complement, with
        an independent floor so it never reads exactly zero. FOC (conflict)
        is high only when entropy AND kappa disagree with each other --
        i.e. the model is both spread out over many candidates *and* those
        candidates point in inconsistent directions.
        """
        h = shannon_entropy(candidate_probabilities)
        kappa = vmf_concentration(candidate_embeddings)

        normalized_entropy = min(h / max(max_expected_entropy_bits, _EPS), 1.0)
        normalized_kappa = 1.0 - math.exp(-kappa / 10.0)  # squashes [0, inf) -> [0, 1)

        rightness = max(0.0, min(1.0, normalized_kappa * (1.0 - normalized_entropy)))
        error = max(0.0, min(1.0, 1.0 - rightness))
        conflict = max(0.0, min(1.0, normalized_entropy * (1.0 - normalized_kappa)))

        return cls(
            shannon_entropy_bits=h,
            dcu_kappa=kappa,
            feeling_of_rightness=rightness,
            feeling_of_error=error,
            feeling_of_conflict=conflict,
        )
