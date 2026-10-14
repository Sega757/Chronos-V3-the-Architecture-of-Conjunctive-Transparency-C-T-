## 2026-03-31 - Vectorizing ALS-IRLS in System 2
**Learning:** `np.dot` and vector ops (`np.minimum`/`np.maximum`) beat Python loops and broadcasting array creation by ~1.47x for iterative robust statistics.
**Action:** Always prefer `np.dot` over `(weights[:, None] * array).sum(axis=0)` for weighted vector combinations.
