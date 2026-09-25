"""Huber-loss M-estimation via alternating location/scale IRLS
(ALS-IRLS): the robust-statistics core of System 2's grounding check.

Given a candidate embedding and a (possibly noisy, possibly adversarial)
set of ground-truth reference embeddings, we do not simply average the
references -- outliers among them would silently corrupt the estimate.
Instead we alternate:

  1. Location step (IRLS): with the scale sigma held fixed, re-estimate
     the robust center mu by iteratively reweighted least squares using
     Huber weights w_i = min(1, delta / |r_i|).
  2. Scale step (ALS): with mu held fixed, re-estimate sigma via the
     median absolute deviation (MAD) of the residuals, which is itself a
     robust (outlier-resistant) scale estimator.

until both converge or a max iteration count is reached. The candidate's
Huber residual is then computed against the converged (mu, sigma).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

DEFAULT_DELTA = 1.345  # standard Huber tuning constant (95% efficiency under Gaussian noise)
_EPS = 1e-9


def huber_loss(residual: float, delta: float = DEFAULT_DELTA) -> float:
    r = abs(residual)
    if r <= delta:
        return 0.5 * r * r
    return delta * (r - 0.5 * delta)


def _huber_weight(residual: float, delta: float) -> float:
    r = abs(residual)
    return 1.0 if r <= delta else delta / max(r, _EPS)


@dataclass(frozen=True)
class RobustEstimate:
    location: np.ndarray
    scale: float
    iterations: int
    converged: bool


def als_irls_estimate(
    reference_embeddings: list[np.ndarray],
    *,
    delta: float = DEFAULT_DELTA,
    max_iterations: int = 50,
    tolerance: float = 1e-6,
) -> RobustEstimate:
    """Compute a robust (mu, sigma) estimate over a set of reference
    embeddings via alternating IRLS location updates and MAD scale
    updates. Requires at least one reference embedding."""
    if not reference_embeddings:
        raise ValueError("als_irls_estimate: at least one reference embedding is required")

    refs = np.stack(reference_embeddings)
    mu = refs.mean(axis=0)
    sigma = 1.0

    converged = False
    iterations = 0
    for iterations in range(1, max_iterations + 1):
        distances = np.linalg.norm(refs - mu, axis=1) / max(sigma, _EPS)
        weights = np.array([_huber_weight(d, delta) for d in distances])
        weight_sum = weights.sum()
        if weight_sum < _EPS:
            break
        new_mu = (weights[:, None] * refs).sum(axis=0) / weight_sum

        residual_norms = np.linalg.norm(refs - new_mu, axis=1)
        mad = np.median(np.abs(residual_norms - np.median(residual_norms)))
        new_sigma = max(1.4826 * mad, _EPS)  # 1.4826 makes MAD consistent for a Gaussian

        shift = np.linalg.norm(new_mu - mu)
        scale_shift = abs(new_sigma - sigma)
        mu, sigma = new_mu, new_sigma
        if shift < tolerance and scale_shift < tolerance:
            converged = True
            break

    return RobustEstimate(location=mu, scale=sigma, iterations=iterations, converged=converged)


def candidate_huber_residual(
    candidate_embedding: np.ndarray,
    reference_embeddings: list[np.ndarray],
    *,
    delta: float = DEFAULT_DELTA,
) -> float:
    """Robust residual of a candidate against the converged reference
    estimate: the (delta-scaled) distance of the candidate from the
    robust center, in units of the robust scale, passed through the Huber
    loss so a small number of near-misses cost little but a large
    deviation is penalized (near-)linearly rather than quadratically."""
    estimate = als_irls_estimate(reference_embeddings, delta=delta)
    normalized_distance = float(np.linalg.norm(candidate_embedding - estimate.location) / max(estimate.scale, _EPS))
    return huber_loss(normalized_distance, delta=delta)
