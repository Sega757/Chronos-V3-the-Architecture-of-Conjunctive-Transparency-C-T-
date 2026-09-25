-- 002_governance_schema.sql
-- L-E-J-D-A-S governance schema: Legitimacy, Efficacy, Justification,
-- Distribution, Accountability, Sanction.

BEGIN;

CREATE TABLE governance_actions (
    action_id              TEXT PRIMARY KEY DEFAULT encode(gen_random_bytes(16), 'hex'),
    subject_id              TEXT NOT NULL,               -- node_id, service name, or policy id
    legitimacy_basis         TEXT NOT NULL,               -- by what authority
    efficacy_metric           TEXT NOT NULL,               -- how outcome is measured
    justification              TEXT NOT NULL,               -- recorded rationale
    distribution_policy        TEXT NOT NULL,               -- who/what it applies to
    accountable_party           TEXT NOT NULL REFERENCES nodes(node_id),
    sanction                     TEXT,                        -- consequence on violation, if any
    created_at                    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_governance_actions_subject ON governance_actions(subject_id);

-- Sanctions actually levied (as opposed to the sanction policy text on a
-- governance_actions row). Distinct table so enforcement history is
-- queryable independent of the policy that authorized it.
CREATE TABLE sanctions (
    sanction_id     BIGSERIAL PRIMARY KEY,
    action_id        TEXT NOT NULL REFERENCES governance_actions(action_id),
    node_id           TEXT NOT NULL REFERENCES nodes(node_id),
    kind              TEXT NOT NULL CHECK (kind IN ('WARNING', 'STAKE_SLASH', 'SUSPENSION', 'REVOCATION')),
    amount             NUMERIC(20, 8),   -- collateral amount slashed, if kind = STAKE_SLASH
    reason              TEXT NOT NULL,
    imposed_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sanctions_node_id ON sanctions(node_id);

COMMIT;
