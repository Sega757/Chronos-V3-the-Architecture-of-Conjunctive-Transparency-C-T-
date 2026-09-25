# Proof-of-Sampling Consensus, Governance, and the Security Perimeter

## Proof-of-Sampling (PoSP) consensus

When System 2 escalates a candidate (`VERIFICATION_VERDICT_ESCALATED`,
because its `feeling_of_conflict` crossed
`FEELING_OF_CONFLICT_ESCALATION_THRESHOLD`), System 0 opens a
**consensus round** (`services/arbiter_module/src/posp_consensus.py`,
`ConsensusEngine.open_round`). Independently registered arbiter nodes each
submit one `ConsensusSample`: a signed vote (`vote_grounded: bool`) backed
by staked collateral (`stake_collateral`).

A round resolves once the total submitted stake reaches a quorum
threshold, or a bounded timeout elapses (`ConsensusEngine.await_resolution`).
Resolution treats the round as a simple stake-weighted game:

```
weighted_yes = Σ stake_i  for samples voting "grounded"
weighted_no  = Σ stake_i  for samples voting "not grounded"

score = | weighted_yes − weighted_no | / (weighted_yes + weighted_no)
```

`score` is reported as the round's **`nash_equilibrium_score`**: it
measures how far the outcome sits from a 50/50 split — i.e. how stable an
equilibrium the independently-staked arbiters converged on. Each arbiter's
individual payoff is highest when its vote matches the eventual majority
(agreement is rewarded, dissent from a decisive majority is
[slashed](#collateral-slashing) — see below), so wide, stake-weighted
agreement approximates a Nash equilibrium of that incentive game.

* `score >= DECISIVENESS_THRESHOLD` (0.20) → the round is decisive:
  `UPHELD` if the majority vote matches the originally contested verdict,
  `OVERTURNED` if it disagrees with it.
* `score < DECISIVENESS_THRESHOLD`, or no stake was submitted before the
  timeout → `DEADLOCKED`. SCCS does not force a decision out of a
  genuinely split arbiter pool; a deadlocked round is escalated further,
  to a human operator, rather than resolved by coin flip.

## Collateral slashing

On a **decisive** outcome, every arbiter node whose vote disagreed with
the resolved majority is slashed `SLASH_FRACTION` (10%) of its staked
collateral (`ConsensusEngine._resolve_locked`, recorded via
`GovernanceRegistry.record_slash`). This is deliberately asymmetric with
a `DEADLOCKED` round, where nobody is slashed: the penalty is for being
confidently wrong in a clear consensus, not for a round that never reached
one. `db/migrations/003_posp_consensus.sql`'s `arbiter_stakes` table is
the durable ledger backing this in a real deployment; the in-memory
`ConsensusEngine` here is the reference implementation of the same rules.

## L-E-J-D-A-S governance schema

Every governance action System 0 takes — a slash, a suspension, a policy
change — is recorded against six required fields
(`proto/arbiter.proto`'s `GovernanceAction`, `db/migrations/002_governance_schema.sql`):

| Field | Answers |
|---|---|
| **L**egitimacy | By what authority is this action taken? |
| **E**fficacy | By what measurable outcome is it judged? |
| **J**ustification | What is the recorded rationale? |
| **D**istribution | Who or what does it apply to? |
| **A**ccountability | Who is answerable for it? |
| **S**anction | What is the consequence if it's violated? |

`GetGovernanceAction` (in `proto/arbiter.proto`'s `MetaArbiter` service)
always answers for any subject, defaulting to an explicit
"no action recorded yet" record rather than an error, so the absence of
governance history is itself legible rather than silent.

## Surrounding security perimeter

Three additional design commitments bound how SCCS is meant to be
deployed, beyond the three core services in this repository:

* **Six-Field Protocol for Absolute Autonomy** — before SCCS is granted
  unsupervised authority over an action, six conditions must all be
  independently satisfiable: (1) the action's `Legitimacy` basis is
  recorded, (2) its `Efficacy` metric is defined *before* the action is
  taken, (3) a `Justification` is attached, (4) its `Distribution` (blast
  radius) is bounded and known in advance, (5) an `Accountable` party is
  named, and (6) a `Sanction` exists for getting it wrong. This is the
  L-E-J-D-A-S schema applied prospectively, as a gate, rather than
  retrospectively as a record.
* **Gateway-Executor isolation** — the process that talks to the outside
  world (the Gateway) and the process that can take consequential action
  (the Executor) are architecturally separate, communicating only over a
  narrow, typed interface (an AIDL-style contract analogous to the gRPC
  contracts in `proto/`), so that a compromised or confused Gateway cannot
  itself invoke an Executor capability directly.
* **Linguistic Facade honeypot sandbox** — an adversarial or
  prompt-injection-style input is first handled inside an isolated
  "facade" that looks and behaves like the real system but has no path to
  any Executor capability, so that probing or exploitation attempts are
  contained and observable rather than reaching anything that matters.

These three are stated here as the governing constraints for any future
Gateway/Executor implementation added to this repository; the three
services currently implemented (System 1, System 2, System 0) sit
entirely on the Executor/verification side of that boundary.
