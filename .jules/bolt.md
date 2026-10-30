## 2026-03-31 - Vectorizing ALS-IRLS in System 2
**Learning:** `np.dot` and vector ops (`np.minimum`/`np.maximum`) beat Python loops and broadcasting array creation by ~1.47x for iterative robust statistics.
**Action:** Always prefer `np.dot` over `(weights[:, None] * array).sum(axis=0)` for weighted vector combinations.

## 2026-03-31 - Fast JSON string escaping in Python
**Learning:** Standard library `json.dumps(value, ensure_ascii=False)` in C is ~6x faster than a Python loop iterating over characters with a lookup dictionary and array appends for RFC 8785 JSON string escaping.
**Action:** Use `json.dumps(s, ensure_ascii=False)` when canonicalizing strings in Python rather than manual character iteration loops.

## 2026-03-31 - Vectorized RNG sampling in NumPy default_rng
**Learning:** `rng.normal(size=(N, DIM))` produces the exact same PRNG sequence as looping `rng.normal(size=DIM)` N times in NumPy `default_rng`, but runs ~1.5x faster due to reduced call overhead and contiguous C allocation.
**Action:** Prefer batch shape tuple arguments over looped single-sample calls when generating reproducible multi-dimensional random arrays.

## 2026-03-31 - Batch epistemic state derivation in System 1
**Learning:** Batching candidate embeddings into a single 2D array and precomputing distribution entropy with `math.log2(N)` yields ~5.75x speedup over calling `EpistemicState.derive` repeatedly in a candidate loop.
**Action:** Vectorize multi-candidate epistemic state derivations across candidate batches rather than computing single-row array slices in per-item loops.

## 2026-03-31 - LRU Caching for Candidate Content Embedding Extraction
**Learning:** Caching candidate content embedding derivation using `@functools.lru_cache` in System 2 Verifier yields >140x speedup by eliminating redundant SHA-256 string hashing, NumPy PRNG instantiation, and vector allocation on recurring content verifications.
**Action:** Cache deterministic content embedding lookups in pure Python services using `functools.lru_cache`.

## 2026-03-31 - Vectorized Huber Weighting and BLAS Dot Product in Chronos Logos
**Learning:** Replacing manual `ones_like`, `outlier_mask`, `safe_res` array allocation and boolean indexing in `chronos_logos` ALS-IRLS with `np.minimum`/`np.maximum` vector ops and `np.dot` BLAS dot product achieves ~1.73x speedup.
**Action:** Use `np.minimum(1.0, delta / np.maximum(abs_res, 1e-8))` for vectorized Huber reweighting instead of creating temporary arrays and boolean mask indexing.

## 2026-03-31 - Ed25519 Public Key Precomputation & LRU Caching in Cryptography
**Learning:** Pre-calculating `public_key_bytes` on `KeyPair` creation and caching `Ed25519PublicKey.from_public_bytes` via `@functools.lru_cache` eliminates redundant OpenSSL C object allocations during repeated signing and verification operations.
**Action:** Always precompute static public key byte representations on key initialization and LRU cache byte-to-key-object parsers in cryptographic hot paths.

## 2026-03-31 - Merkle Tree Level Pre-padding and Array Re-allocation Elimination
**Learning:** Pre-padding odd-length levels in-place when constructing a Merkle tree ensures stored levels are pre-balanced, eliminating redundant list allocations (`level + [level[-1]]`) during inclusion proof generation and yielding ~2.4x speedup.
**Action:** Always pad odd tree levels during initial tree materialization so query methods like `proof()` can operate directly on even-length level slices without temporary list copies.

## 2026-03-31 - Vectorized vMF Dispersion via Reciprocal Norm BLAS Dot Product
**Learning:** In `vmf_concentration`, replacing 2D matrix broadcasting division (`unit_vectors / norms`) and `sum(axis=0)` with 1D reciprocal norm vector division (`1.0 / norms`) and `np.dot` BLAS vector product reduces division operations from N*P to N and eliminates intermediate (N, P) matrix allocations, yielding a 1.22x–1.69x speedup.
**Action:** Prefer `np.dot(1.0 / np.linalg.norm(X, axis=1), X)` over `(X / np.linalg.norm(X, axis=1, keepdims=True)).sum(axis=0)` when computing directional sums of 2D vector arrays.
