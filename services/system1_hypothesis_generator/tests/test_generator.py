import pytest

from src.exceptions import GenerationBackendError
from src.generator import DeterministicStubModel


def test_sample_is_deterministic_for_same_query():
    model = DeterministicStubModel()
    first = model.sample("what is conjunctive transparency", 4, 1.0)
    second = model.sample("what is conjunctive transparency", 4, 1.0)
    assert [c.content for c in first] == [c.content for c in second]
    assert [c.probability for c in first] == [c.probability for c in second]


def test_sample_probabilities_sum_to_one():
    model = DeterministicStubModel()
    candidates = model.sample("hello", 5, 0.7)
    assert sum(c.probability for c in candidates) == pytest.approx(1.0, rel=1e-6)


def test_sample_rejects_empty_query():
    model = DeterministicStubModel()
    with pytest.raises(GenerationBackendError):
        model.sample("   ", 4, 1.0)
