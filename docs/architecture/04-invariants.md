# Invariants

These are the properties every implementation in this repository is
required to uphold. Each is numbered so it can be referenced from code
comments, PR descriptions, and review checklists. "Enforced in" points to
the code that makes the invariant true today; a change to that code that
weakens the invariant should be treated as a breaking change requiring
explicit sign-off, not a routine refactor.

## INV-1 — No unverified hypothesis crosses the trust boundary

A `HypothesisCandidate` produced by System 1 must never reach an external
caller, or be treated as authoritative by any subsystem, without first
passing through `chronos.v3.system2.ChronosVerifier/Verify` (or
`BatchVerify`).

* **Enforced in:** process/network separation between
  `services/system1_hypothesis_generator` and
  `services/system2_chronos_verifier` — there is no shared memory or RPC
  path from System 1 directly to an external boundary. See
  `proto/system1_hypothesis.proto`'s service-level comment.

## INV-2 — GROUNDED is reachable only through the zero-hallucination lock

A `VerificationVerdict` of `GROUNDED` may only be produced by
`decide_verdict()` in
`services/system2_chronos_verifier/src/zero_hallucination.py`, and only
when all of the following hold:

1. `ground_truth_refs` was non-empty on the request.
2. A Huber residual against the robust (ALS-IRLS) ground-truth estimate
   was successfully computed.
3. That residual is `<= HUBER_RESIDUAL_GROUNDED_MAX`.
4. The candidate's `feeling_of_conflict` is below
   `FEELING_OF_CONFLICT_ESCALATION_THRESHOLD` (otherwise the result is
   `ESCALATED`, not decided unilaterally).

Any failure in resolving ground truth (`GroundTruthUnavailableError`)
fails **closed** to `REJECTED`, never silently to `GROUNDED`.

* **Enforced in:** `services/system2_chronos_verifier/src/zero_hallucination.py`,
  exercised by `services/system2_chronos_verifier/tests/test_zero_hallucination.py`.

## INV-3 — Every cross-boundary artifact is signed over its canonical form

Any `Provenance`, `VerificationResult`, or `ArbitrationDecision` that
leaves a service process carries an Ed25519 `Signature` computed over the
SHA-256 hash of the artifact's RFC 8785 canonical JSON encoding. A
signing failure aborts the RPC (`SigningError` → `grpc.StatusCode.INTERNAL`)
rather than returning an unsigned result.

* **Enforced in:** `libs/chronos_common/chronos_common/signing.py`,
  invoked from each service's `src/server.py` before constructing its
  response message.

## INV-4 — A decisive PoSP outcome always resolves to UPHELD, OVERTURNED, or a recorded slash — never silently

Once a consensus round crosses `DECISIVENESS_THRESHOLD`, the outcome
(`UPHELD` / `OVERTURNED`) and every dissenting node's slash are computed
together, atomically, under the round's lock — there is no window where
an outcome is decided but its slashing consequences are not yet recorded.

* **Enforced in:** `services/arbiter_module/src/posp_consensus.py`,
  `ConsensusEngine._resolve_locked`.

## INV-5 — A deadlocked round slashes nobody

If a round's stake-weighted score never reaches `DECISIVENESS_THRESHOLD`
(including the zero-samples-before-timeout case), no node is slashed. The
penalty in PoSP consensus is for being confidently wrong in a clear
majority, not for participating in a round that stayed genuinely
contested.

* **Enforced in:** `services/arbiter_module/src/posp_consensus.py`,
  `ConsensusEngine._resolve_locked`; exercised by
  `services/arbiter_module/tests/test_posp_consensus.py::test_close_split_is_deadlocked_and_nobody_is_slashed`
  and `::test_no_samples_before_timeout_is_deadlocked`.

## INV-6 — GetGovernanceAction never errors on an unknown subject

Governance history absence is represented explicitly (a default record
whose `justification` states no action has been recorded), not by an RPC
error — an auditor querying an unfamiliar subject_id gets a legible answer,
not a failure to distinguish from a transient outage.

* **Enforced in:** `services/arbiter_module/src/governance.py`,
  `GovernanceRegistry.get`.

## INV-7 — All hashing and signing use one canonical encoding

There is exactly one canonicalization routine in the codebase
(`chronos_common.canonicalize`, RFC 8785), imported by every module that
hashes or signs a payload. No service implements its own JSON
serialization for hashing purposes.

* **Enforced in:** `libs/chronos_common/chronos_common/canonical_json.py`
  is the sole import site used by `merkle.py` (indirectly, via callers)
  and `signing.py` across all three services.
