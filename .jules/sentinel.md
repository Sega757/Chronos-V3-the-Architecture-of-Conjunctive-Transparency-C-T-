# Sentinel Security Journal

## 2026-10-14 - Unauthenticated Inter-Service Candidate Verification
**Vulnerability:** System 2 (verifier) received `HypothesisCandidate` payloads over gRPC and processed them without verifying the attached Ed25519 signature in `candidate.provenance.signatures`.
**Learning:** In a multi-agent system, signing messages at emission (System 1) is ineffective if downstream services (System 2) assume trust and do not explicitly verify signatures prior to execution.
**Prevention:** Always verify incoming payload signatures against the claimed public key at the service boundary before performing verification calculations or state transitions.
