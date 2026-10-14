## 2025-02-17 - Vectorizing NumPy conditional weights in iterative solvers

**Learning:** Un-vectorized list comprehensions calculating scalar weights inside iterative loops (like ALS-IRLS) add significant overhead. When vectorizing with `np.where`, both branches are evaluated, so the alternative branch must use `np.maximum(x, _EPS)` to avoid `RuntimeWarning: divide by zero`.

**Action:** Vectorize array element-wise conditionally using `np.where` with denominator floor protection `np.maximum(denom, _EPS)`.
