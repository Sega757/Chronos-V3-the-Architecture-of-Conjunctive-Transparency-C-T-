-- 003_posp_consensus.sql
-- Proof-of-Sampling (PoSP) consensus rounds, run by System 0 (Meta-Arbiter)
-- to resolve escalations raised by System 2 (high Feeling-of-Conflict).

BEGIN;

CREATE TABLE arbiter_stakes (
    node_id             TEXT PRIMARY KEY REFERENCES nodes(node_id),
    collateral_balance  NUMERIC(20, 8) NOT NULL DEFAULT 0 CHECK (collateral_balance >= 0),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE consensus_rounds (
    round_id                    TEXT PRIMARY KEY,
    candidate_id                 TEXT NOT NULL REFERENCES hypotheses(candidate_id),
    contested_verdict             TEXT NOT NULL CHECK (contested_verdict IN ('GROUNDED', 'REJECTED', 'ESCALATED')),
    escalation_reason              TEXT NOT NULL,
    status                          TEXT NOT NULL DEFAULT 'OPEN'
                                        CHECK (status IN ('OPEN', 'UPHELD', 'OVERTURNED', 'DEADLOCKED')),
    nash_equilibrium_score           DOUBLE PRECISION,
    decision_merkle_hash               BYTEA,
    opened_at                            TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at                             TIMESTAMPTZ
);

CREATE TABLE consensus_samples (
    id                   BIGSERIAL PRIMARY KEY,
    round_id              TEXT NOT NULL REFERENCES consensus_rounds(round_id),
    arbiter_node_id        TEXT NOT NULL REFERENCES nodes(node_id),
    vote_grounded            BOOLEAN NOT NULL,
    stake_collateral          NUMERIC(20, 8) NOT NULL CHECK (stake_collateral > 0),
    signature                  BYTEA NOT NULL,
    submitted_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (round_id, arbiter_node_id)
);

CREATE INDEX idx_consensus_samples_round_id ON consensus_samples(round_id);

COMMIT;
