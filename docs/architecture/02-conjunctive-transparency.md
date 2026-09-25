# Conjunctive Transparency (C-T)

**Conjunctive Transparency** is the requirement that a claim's *content*
and the *evidence for it* travel together, conjunctively, as one signed,
hashable unit — never as content alone with evidence promised
"available on request." A claim without its evidence attached is not
trusted to gain evidence later; it is treated as ungrounded now.

Three mechanisms implement C-T in this codebase: quantified epistemic
state, canonical hashing + signing, and an append-only Merkle-chained
audit log.

## 1. Epistemic state (the "how sure, and why" attached to every hypothesis)

Defined in `proto/common.proto` as `EpistemicState`, computed in
`libs/chronos_common/chronos_common/epistemics.py`:

* **Shannon entropy `H(X)`** — the information-theoretic spread of System
  1's sampling distribution over candidates, in bits:

  ```
  H(X) = - Σ p_i · log2(p_i)
  ```

  Low entropy means System 1's sampling concentrated on a small set of
  candidates; high entropy means it spread mass broadly (i.e. it wasn't
  sure).

* **Directional Consistency Uncertainty (DCU)**, via a von Mises-Fisher
  concentration estimate `kappa` over the candidates' embedding vectors:

  ```
  R̄ = |Σ x̂_i| / n
  kappa ≈ R̄ · (p − R̄²) / (1 − R̄²)
  ```

  (Banerjee et al. 2005 approximation.) High `kappa` means the candidate
  embeddings point in a consistent direction on the unit sphere — the
  underlying signal agrees with itself; `kappa → 0` as they scatter
  toward uniform.

* **FOR / FOE / FOC** — Feeling of Rightness, Feeling of Error, Feeling of
  Conflict, each in `[0, 1]`, derived from the two signals above
  (`EpistemicState.derive`): rightness rises with directional consistency
  and falls with normalized entropy; conflict is high specifically when
  entropy and consistency *disagree* with each other (spread out *and*
  inconsistent), which is the signal System 2 uses to decide whether to
  escalate to System 0 rather than decide alone.

Epistemic state is informative, never authoritative: it travels with
every `HypothesisCandidate`, but System 2's zero-hallucination lock
(`services/system2_chronos_verifier/src/zero_hallucination.py`) never
grounds a candidate on FOR/FOE/FOC alone — it only uses `feeling_of_conflict`
to decide whether to escalate, never to decide `GROUNDED`.

## 2. Canonical hashing and signing

Two problems have to be solved before "signed evidence" means anything:

1. **Two semantically-identical payloads must hash identically**,
   regardless of which language, JSON library, or key-insertion order
   produced them. Solved by `chronos_common/canonical_json.py`, an
   implementation of **RFC 8785 (JSON Canonicalization Scheme)**: object
   keys are sorted, numbers use a canonical shortest-round-trip form, and
   there is no insignificant whitespace.
2. **A hash alone can be replayed or forged.** Solved by
   `chronos_common/signing.py`: every payload is SHA-256 hashed
   (over its canonical encoding) and then **Ed25519**-signed by the
   producing node's private key. The resulting `Signature` message
   (`proto/common.proto`) carries the signer's id, its public key, the
   signature bytes, and the payload hash — enough for any downstream
   party to independently re-verify it without calling back to the
   signer.

Every cross-boundary artifact in SCCS — a `HypothesisCandidate`'s
`Provenance`, a `VerificationResult`'s `verifier_signature`, an
`ArbitrationDecision`'s `decision_merkle_hash` — is built this way.

## 3. The Merkle-chained audit log

`db/migrations/001_init.sql` defines `audit_log` as an append-only table
where each row's `leaf_hash` is the SHA-256 digest of its own
canonicalized payload, and `prev_hash` links it to the row before it —
a hash chain. System 2's `BatchVerify` additionally folds a whole batch
of `VerificationResult`s into a single `batch_merkle_root`
(`chronos_common/merkle.py`, `MerkleTree` / `merkle_root`), so an auditor
can verify that a specific result was part of a specific batch using a
proof of logarithmic size (`MerkleTree.proof` / `verify_proof`) rather
than replaying the whole batch.

Together, these three mechanisms mean that by the time any claim reaches
a trust boundary, it carries: *what* is being claimed, *how confident* the
producer was and on what basis, *whether* it was independently verified
against ground truth (or by whom, if arbitrated), and a *cryptographic,
tamper-evident* record of all of the above. That conjunction — content
plus evidence, inseparably — is Conjunctive Transparency.
