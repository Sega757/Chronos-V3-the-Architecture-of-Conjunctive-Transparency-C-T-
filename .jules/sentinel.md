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
