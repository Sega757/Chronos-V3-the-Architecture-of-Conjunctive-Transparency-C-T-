import numpy as np

from src.robust_stats import als_irls_estimate, candidate_huber_residual, huber_loss


def test_huber_loss_is_quadratic_within_delta():
    assert huber_loss(0.5, delta=1.345) == 0.5 * 0.5 * 0.5


def test_huber_loss_is_linear_beyond_delta():
    delta = 1.0
    r = 3.0
    assert huber_loss(r, delta=delta) == delta * (r - 0.5 * delta)


def test_als_irls_recovers_clean_cluster_mean():
    rng = np.random.default_rng(0)
    true_mean = np.array([1.0, -2.0, 0.5])
    refs = [true_mean + rng.normal(scale=0.01, size=3) for _ in range(20)]
    estimate = als_irls_estimate(refs)
    assert np.allclose(estimate.location, true_mean, atol=0.1)


def test_als_irls_is_robust_to_outliers():
    rng = np.random.default_rng(1)
    true_mean = np.zeros(4)
    refs = [true_mean + rng.normal(scale=0.01, size=4) for _ in range(18)]
    # Add a couple of wild outliers far from the cluster.
    refs += [np.full(4, 100.0), np.full(4, -100.0)]
    estimate = als_irls_estimate(refs)
    assert np.linalg.norm(estimate.location - true_mean) < 1.0


def test_candidate_matching_cluster_has_low_residual():
    # A larger reference sample is used here (vs. the other tests in this
    # file) so the ALS-IRLS location estimate converges tight enough that
    # an exact-match candidate's residual is unambiguously small -- with
    # only a handful of references, the location estimate's own sampling
    # noise is on the same order as the residual scale, so "low residual"
    # would not be a meaningful assertion.
    rng = np.random.default_rng(2)
    true_mean = np.array([0.2, 0.3])
    refs = [true_mean + rng.normal(scale=0.01, size=2) for _ in range(200)]
    residual = candidate_huber_residual(true_mean, refs)
    assert residual < 0.1


def test_candidate_far_from_cluster_has_high_residual():
    rng = np.random.default_rng(3)
    true_mean = np.array([0.0, 0.0])
    refs = [true_mean + rng.normal(scale=0.01, size=2) for _ in range(10)]
    far_candidate = np.array([50.0, 50.0])
    residual = candidate_huber_residual(far_candidate, refs)
    assert residual > 10.0
