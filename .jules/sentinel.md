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

## 2026-10-19 - Identity Verification Bypass via Empty Signer ID Guard
**Vulnerability:** Services guarded signature identity checks with `if sig.signer_id and ...`, allowing callers to omit `signer_id` (`""`) and bypass node identity checks completely while submitting valid signatures signed by arbitrary keypairs.
**Learning:** Using truthiness guards (`if string_field and ...`) on optional/default string fields in identity checks creates a bypass whenever the field is empty or unset.
**Prevention:** Avoid truthiness guards on identity fields; always directly enforce equality between the payload signature's claimed `signer_id` and the declared node ID (`sig.signer_id == target_node_id`).
