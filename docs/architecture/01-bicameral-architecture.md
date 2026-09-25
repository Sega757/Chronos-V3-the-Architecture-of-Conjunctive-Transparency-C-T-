# Bicameral Architecture: System 1, System 2, System 0

SCCS borrows its naming from dual-process theories of cognition (System 1
"fast thinking" / System 2 "slow thinking"), and adds a third,
meta-governance layer, System 0, that neither System 1 nor System 2 has
authority over the other's disputes without it.

```
                         ┌─────────────────────────────┐
   external query  ───▶  │   System 1: Neocortex        │
                         │   (Stochastic Hypothesis      │
                         │    Generator)                 │
                         │   proto/system1_hypothesis.proto│
                         └───────────────┬───────────────┘
                                          │  HypothesisCandidate
                                          │  (signed, provenance-tagged,
                                          │   NEVER exposed externally)
                                          ▼
                         ┌─────────────────────────────┐
                         │   System 2: Chronos Engine    │
                         │   (Deterministic Ground-Truth │
                         │    Verifier / "Thought Layer")│
                         │   proto/system2_verifier.proto│
                         └───────┬───────────────┬───────┘
                    GROUNDED /   │               │  ESCALATED
                    REJECTED     │               │  (Feeling-of-Conflict
                                 │               │   too high)
                                 ▼               ▼
                    external boundary   ┌─────────────────────────────┐
                    (only GROUNDED      │   System 0: Meta-Arbiter      │
                    results may pass)   │   (PoSP consensus +           │
                                        │    L-E-J-D-A-S governance)    │
                                        │   proto/arbiter.proto         │
                                        └───────────────┬───────────────┘
                                                         │ UPHELD / OVERTURNED
                                                         │ / DEADLOCKED
                                                         ▼
                                            back to the System 2 boundary
                                            (DEADLOCKED escalates further,
                                             to a human operator)
```

## System 1 — Neocortex (Stochastic Hypothesis Generator)

* **Job:** given a query, propose a bounded set of candidate hypotheses
  quickly and cheaply. Optimizes for recall, not precision.
* **Output:** a `HypothesisCandidate` per proto/system1_hypothesis.proto,
  always carrying an `EpistemicState` (Shannon entropy, DCU/kappa, FOR,
  FOE, FOC — see [`02-conjunctive-transparency.md`](02-conjunctive-transparency.md))
  and a signed `Provenance` envelope.
* **What it must never do:** answer an external caller directly, or claim
  that any candidate is true. System 1 proposes; it never asserts.
* **Reference implementation:** [`services/system1_hypothesis_generator`](../../services/system1_hypothesis_generator).
  `src/generator.py` defines the `HypothesisModel` seam a real model plugs
  into; the shipped `DeterministicStubModel` exists only so the pipeline
  is runnable and testable without a model dependency.

## System 2 — Chronos Engine (Deterministic Ground-Truth Verifier)

* **Job:** take every candidate System 1 produces and decide, using
  deterministic, auditable methods, whether it is grounded in verified
  knowledge.
* **Method:** robust M-estimation. Ground-truth reference embeddings are
  fit with an alternating location/scale IRLS procedure (ALS-IRLS, see
  `services/system2_chronos_verifier/src/robust_stats.py`) using a Huber
  loss, so a handful of outlier or adversarial references cannot silently
  drag the estimate off target. The candidate's Huber residual against
  that robust estimate is the primary grounding signal.
* **The zero-hallucination lock:** `src/zero_hallucination.py` is the
  single function in the entire codebase allowed to produce a `GROUNDED`
  verdict, and it can only do so when ground-truth references were
  actually supplied and the residual is within tolerance. No code path —
  not a missing reference, not a backend error, not a high-confidence
  System 1 candidate — can produce `GROUNDED` any other way. See
  [`04-invariants.md#inv-2`](04-invariants.md).
* **Escalation:** when a candidate's own `feeling_of_conflict` is high,
  System 2 does not guess — it returns `ESCALATED` and the caller routes
  the contested result to System 0.
* **Reference implementation:** [`services/system2_chronos_verifier`](../../services/system2_chronos_verifier).

## System 0 — Meta-Arbiter

* **Job:** resolve `ESCALATED` verdicts through Proof-of-Sampling (PoSP)
  consensus among independently staked arbiter nodes, and hold the
  L-E-J-D-A-S governance record for every subject (node, service, or
  policy) in the system.
* **Method:** see [`03-posp-consensus.md`](03-posp-consensus.md) for the
  full consensus and slashing model.
* **Reference implementation:** [`services/arbiter_module`](../../services/arbiter_module).

## Interface boundaries

Each subsystem is a **separate gRPC service with its own process
boundary**, deliberately — not an in-process module boundary that
discipline alone enforces. This means:

* System 1's generated candidates physically cannot reach an external
  caller without going over the wire to System 2 first; there is no shared
  memory or shared object graph to smuggle a shortcut through.
* System 2's verdicts are independently signed (Ed25519) before they leave
  its process, so a compromised or buggy downstream consumer cannot fake a
  `GROUNDED` verdict — it can only refuse to honor a genuine one.
* System 0's arbitration decisions are similarly signed and hashed into
  the audit log's Merkle chain.

This is also why the proto contracts (`proto/*.proto`) are the actual
source of truth for what one subsystem is allowed to say to another — see
[`04-invariants.md`](04-invariants.md) for the invariants those contracts
are designed to make impossible to violate.
