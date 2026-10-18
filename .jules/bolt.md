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

## 2026-03-31 - Reusing residual norms across ALS-IRLS iterations
**Learning:** In iterative location/scale estimation, precomputing initial residual norms and reusing `residual_norms` from step k in step k+1 avoids recomputing `np.linalg.norm(refs - mu, axis=1)` from scratch every iteration, yielding a ~14%-33% speedup.
**Action:** Check iterative optimization loops for state that was already computed at the end of the previous iteration before recalculating it from scratch.
