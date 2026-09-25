-- 001_init.sql
-- Core SCCS tables: nodes, hypotheses, verifications, and the Merkle-chained
-- audit log. Target: PostgreSQL 15+.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Registered nodes across all three subsystems (System 1 generators,
-- System 2 verifiers, System 0 arbiters). arbiter nodes additionally carry
-- staked collateral (see 003_posp_consensus.sql).
CREATE TABLE nodes (
    node_id         TEXT PRIMARY KEY,
    role            TEXT NOT NULL CHECK (role IN ('system1', 'system2', 'arbiter', 'gateway')),
    public_key      BYTEA NOT NULL,      -- Ed25519 public key, 32 bytes
    display_name    TEXT,
    registered_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_active       BOOLEAN NOT NULL DEFAULT true
);

-- Hypotheses emitted by System 1. Never authoritative on their own.
CREATE TABLE hypotheses (
    candidate_id            TEXT PRIMARY KEY,
    batch_id                TEXT NOT NULL,
    origin_node_id          TEXT NOT NULL REFERENCES nodes(node_id),
    trace_id                TEXT NOT NULL,
    content                 TEXT NOT NULL,
    shannon_entropy_bits    DOUBLE PRECISION NOT NULL,
    dcu_kappa               DOUBLE PRECISION NOT NULL,
    feeling_of_rightness    DOUBLE PRECISION NOT NULL CHECK (feeling_of_rightness BETWEEN 0 AND 1),
    feeling_of_error        DOUBLE PRECISION NOT NULL CHECK (feeling_of_error BETWEEN 0 AND 1),
    feeling_of_conflict     DOUBLE PRECISION NOT NULL CHECK (feeling_of_conflict BETWEEN 0 AND 1),
    supporting_features     JSONB NOT NULL DEFAULT '{}'::jsonb,
    content_hash            BYTEA NOT NULL,   -- SHA-256 over RFC 8785 canonical JSON
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_hypotheses_batch_id ON hypotheses(batch_id);
CREATE INDEX idx_hypotheses_trace_id ON hypotheses(trace_id);

-- Verification verdicts issued by System 2 for a given hypothesis.
-- A GROUNDED verdict is only ever inserted with a non-empty
-- ground_truth_refs array -- enforced in application code by the
-- zero-hallucination lock, and defensively here via CHECK.
CREATE TABLE verifications (
    candidate_id        TEXT PRIMARY KEY REFERENCES hypotheses(candidate_id),
    verifier_node_id    TEXT NOT NULL REFERENCES nodes(node_id),
    verdict              TEXT NOT NULL CHECK (verdict IN ('GROUNDED', 'REJECTED', 'ESCALATED')),
    ground_truth_refs    TEXT[] NOT NULL DEFAULT '{}',
    huber_residual        DOUBLE PRECISION,
    rationale             TEXT NOT NULL,
    merkle_leaf_hash       BYTEA NOT NULL,
    verifier_signature     BYTEA NOT NULL,   -- Ed25519 signature, 64 bytes
    verified_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT grounded_requires_refs
        CHECK (verdict <> 'GROUNDED' OR array_length(ground_truth_refs, 1) > 0)
);

CREATE INDEX idx_verifications_verdict ON verifications(verdict);

-- Append-only, hash-chained audit log. Every row's leaf_hash is a SHA-256
-- digest of its canonicalized payload; prev_hash links it to the previous
-- row, forming a Merkle chain that makes tampering with history detectable.
CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    subsystem       TEXT NOT NULL CHECK (subsystem IN ('system1', 'system2', 'arbiter', 'governance')),
    event_type      TEXT NOT NULL,
    payload         JSONB NOT NULL,
    leaf_hash       BYTEA NOT NULL,
    prev_hash       BYTEA,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_log_subsystem ON audit_log(subsystem);
CREATE UNIQUE INDEX idx_audit_log_leaf_hash ON audit_log(leaf_hash);

COMMIT;
