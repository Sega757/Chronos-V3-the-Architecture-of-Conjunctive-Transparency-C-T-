# Sentinel Security Journal

## 2026-10-14 - Unauthenticated Inter-Service Candidate Verification
**Vulnerability:** System 2 (verifier) received `HypothesisCandidate` payloads over gRPC and processed them without verifying the attached Ed25519 signature in `candidate.provenance.signatures`.
**Learning:** In a multi-agent system, signing messages at emission (System 1) is ineffective if downstream services (System 2) assume trust and do not explicitly verify signatures prior to execution.
**Prevention:** Always verify incoming payload signatures against the claimed public key at the service boundary before performing verification calculations or state transitions.

## 2026-10-15 - Unverified Consensus Sample Submissions
**Vulnerability:** System 0 (MetaArbiter) received `ConsensusSample` payloads over gRPC and processed votes/collateral without verifying the attached Ed25519 `signature` field on the sample request.
**Learning:** In PoSP consensus, accepting votes without boundary Ed25519 verification allows unauthenticated parties to forge votes and alter arbitration outcomes.
**Prevention:** Explicitly verify `ConsensusSample.signature` against canonical sample fields at the gRPC service boundary in `SubmitSample`.

## 2026-10-16 - Unauthenticated Escalation of Contested Verification Results
**Vulnerability:** System 0 (MetaArbiter) received `EscalationRequest` containing a `contested_result` (`VerificationResult`) and opened consensus rounds without verifying the attached `verifier_signature`.
**Learning:** Accepting inter-service escalation requests without boundary signature verification allows unauthenticated or malformed inputs to trigger PoSP consensus rounds and arbitrary stake slashing.
**Prevention:** Verify `contested_result.verifier_signature` against canonical `VerificationResult` fields at the gRPC service boundary in `Escalate`.

## 2026-10-17 - Origin Node Identity Spoofing via Unmatched Signer ID
**Vulnerability:** System 2 (verifier) verified Ed25519 signatures on `HypothesisCandidate` payloads without verifying that `sig.signer_id` matched `candidate.provenance.origin_node_id`.
**Learning:** Signature verification confirms cryptographic key ownership over a payload digest, but does not guarantee authorization or provenance unless the signature's claimed `signer_id` is validated against the payload's declared `origin_node_id`.
**Prevention:** Always assert that `sig.signer_id == origin_node_id` at service boundaries when verifying cryptographic provenance.

## 2026-10-18 - Arbiter Node Identity Spoofing via Unmatched Signer ID in SubmitSample
**Vulnerability:** System 0 (MetaArbiter) verified Ed25519 signatures on `ConsensusSample` payloads without checking that `request.signature.signer_id` matched `request.arbiter_node_id`.
**Learning:** In consensus voting, verifying key signature over a payload containing a target `arbiter_node_id` allows any valid signing key to impersonate another node unless the signature's claimed `signer_id` is explicitly matched to the voting `arbiter_node_id`.
**Prevention:** Always check `request.signature.signer_id == request.arbiter_node_id` when processing signed consensus votes.

## 2026-10-19 - Identity Verification Bypass via Empty Proto String Fields
**Vulnerability:** `if sig.signer_id and sig.signer_id != target_node_id:` skipped identity assertion when `sig.signer_id` was empty (`""`), allowing unsigned or empty `signer_id` signatures to bypass node identity checks.
**Learning:** Checking the truthiness of string fields in Protobuf before performing inequality assertions introduces security bypasses whenever empty string `""` is a falsy default value.
**Prevention:** Never guard identity checks with `if signer_id:`. Always perform direct equality/inequality comparison `if signer_id != target_id:`.

## 2026-11-03 - Unrestricted Verification Verdict Escalation to PoSP Arbitration
**Vulnerability:** System 0 (MetaArbiter) accepted `EscalationRequest` containing arbitrary `VerificationResult` verdicts (such as `GROUNDED` or `REJECTED`) instead of strictly requiring `VERIFICATION_VERDICT_ESCALATED`.
**Learning:** Without checking boundary payload state preconditions (such as verdict state), arbitrary valid signatures on finalized verdicts can be leveraged to re-open consensus rounds, potentially overturning deterministic verifier verdicts and triggering collateral slashing.
**Prevention:** Enforce domain-level invariant validation at the service entrypoint (e.g. `contested.verdict == VERIFICATION_VERDICT_ESCALATED`) in addition to cryptographic signature validation.

## 2026-11-09 - Provenance Origin Node Identity Verification Bypass via Empty Proto Fields
**Vulnerability:** System 2 (verifier) asserted `sig.signer_id != candidate.provenance.origin_node_id` without verifying that `origin_node_id` was non-empty. When both `candidate.provenance.origin_node_id` and `sig.signer_id` were empty (`""`), the equality check evaluated to `True` (`"" == ""`), allowing unauthenticated or anonymous candidates to bypass identity verification.
**Learning:** Directly comparing two string fields without asserting that the reference identity is non-empty allows callers to bypass authentication by providing empty default Protobuf values for both fields.
**Prevention:** Always assert that the declared entity identity (e.g., `origin_node_id`) is non-empty and non-whitespace before comparing against signature metadata at the service boundary.

## 2026-11-10 - NaN / Non-Finite Stake Collateral Consensus Manipulation
**Vulnerability:** System 0 (MetaArbiter) accepted `ConsensusSample` payloads with `NaN` or infinite float values in `stake_collateral` because `request.stake_collateral <= 0` evaluates to `False` for `float('nan')`.
**Learning:** IEEE 754 floating-point comparisons (`<= 0`) fail silently for NaN values. Propagating NaN into stake aggregation and decisiveness calculations corrupts the Nash equilibrium score and consensus resolution.
**Prevention:** Always check `math.isfinite()` on numeric inputs representing financial or voting stakes at service boundaries.
