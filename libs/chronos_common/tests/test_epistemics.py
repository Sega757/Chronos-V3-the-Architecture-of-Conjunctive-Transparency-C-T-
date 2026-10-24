import pytest
import numpy as np

from chronos_common.epistemics import (
    EpistemicState,
    shannon_entropy,
    vmf_concentration,
)


def test_shannon_entropy_valid():
    probs = [0.25, 0.25, 0.25, 0.25]
    h = shannon_entropy(probs)
    assert pytest.approx(h, abs=1e-5) == 2.0


def test_shannon_entropy_zero_probabilities():
    probs = [1.0, 0.0, 0.0]
    h = shannon_entropy(probs)
    assert pytest.approx(h, abs=1e-5) == 0.0


def test_shannon_entropy_invalid_sum():
    with pytest.raises(ValueError, match="probabilities must sum to > 0"):
        shannon_entropy([0.0, 0.0])


def test_vmf_concentration_invalid_shape():
    with pytest.raises(ValueError, match="expected a non-empty \\(n, p\\) array"):
        vmf_concentration(np.array([]))

    with pytest.raises(ValueError, match="expected a non-empty \\(n, p\\) array"):
        vmf_concentration(np.ones((5,)))


def test_vmf_concentration_zero_vectors():
    zeros = np.zeros((10, 16))
    kappa = vmf_concentration(zeros)
    assert kappa == 0.0


def test_vmf_concentration_aligned_vectors():
    # Perfectly aligned unit vectors should yield high concentration / kappa
    vecs = np.tile([1.0, 0.0, 0.0, 0.0], (10, 1))
    kappa = vmf_concentration(vecs)
    assert kappa > 100.0


def test_epistemic_state_derive():
    probs = [0.5, 0.5]
    embeddings = np.array([[1.0, 0.0], [1.0, 0.0]])
    state = EpistemicState.derive(
        candidate_probabilities=probs,
        candidate_embeddings=embeddings,
        max_expected_entropy_bits=1.0,
    )
    assert pytest.approx(state.shannon_entropy_bits, abs=1e-5) == 1.0
    assert state.dcu_kappa > 100.0
    assert 0.0 <= state.feeling_of_rightness <= 1.0
    assert 0.0 <= state.feeling_of_error <= 1.0
    assert 0.0 <= state.feeling_of_conflict <= 1.0
