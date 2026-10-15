## 2026-03-31 - Vectorizing ALS-IRLS in System 2
**Learning:** `np.dot` and vector ops (`np.minimum`/`np.maximum`) beat Python loops and broadcasting array creation by ~1.47x for iterative robust statistics.
**Action:** Always prefer `np.dot` over `(weights[:, None] * array).sum(axis=0)` for weighted vector combinations.

## 2026-03-31 - Fast JSON string escaping in Python
**Learning:** Standard library `json.dumps(value, ensure_ascii=False)` in C is ~6x faster than a Python loop iterating over characters with a lookup dictionary and array appends for RFC 8785 JSON string escaping.
**Action:** Use `json.dumps(s, ensure_ascii=False)` when canonicalizing strings in Python rather than manual character iteration loops.
