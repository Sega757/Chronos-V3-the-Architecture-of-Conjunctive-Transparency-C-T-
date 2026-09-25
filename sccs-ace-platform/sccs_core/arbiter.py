import numpy as np

def calculate_shannon_entropy(probabilities):
    """
    Calculates Shannon Entropy H(X) for a given probability distribution.
    H(X) = -sum( P(x_i) * log2(P(x_i)) )
    """
    probs = np.array(probabilities)
    # Filter out 0 to avoid log2(0)
    probs = probs[probs > 0]
    return -np.sum(probs * np.log2(probs))

def calculate_dcu_variance(embeddings):
    """
    Calculates Directional Consistency Uncertainty (DCU) using
    von Mises-Fisher (vMF) dispersion.
    DCU_variance = 1 - || v_bar ||
    """
    if not embeddings:
        return 0.0

    vectors = np.array(embeddings)
    # Normalize vectors
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    safe_norms = np.where(norms == 0, 1e-8, norms)
    normalized = vectors / safe_norms

    # Mean vector
    v_bar = np.mean(normalized, axis=0)

    # Variance
    return 1.0 - np.linalg.norm(v_bar)

class MetaArbiter:
    def __init__(self, tau_high=2.20, dcu_jailbreak=0.65):
        self.tau_high = tau_high
        self.dcu_jailbreak = dcu_jailbreak

    def evaluate_state(self, probabilities, embeddings=None, prm_score=1.0):
        entropy = calculate_shannon_entropy(probabilities)
        dcu = calculate_dcu_variance(embeddings) if embeddings else 0.0

        # Check Failures
        if dcu > self.dcu_jailbreak:
            return "LINGUISTIC_FACADE", entropy, dcu

        if entropy > self.tau_high or prm_score < 0.80:
            return "METACOGNITIVE_PAUSE", entropy, dcu

        return "HEURISTIC_FAST_PATH", entropy, dcu
