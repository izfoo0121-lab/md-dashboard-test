-- Frozen monthly patronage rate baselines and closing values per agent
CREATE TABLE IF NOT EXISTS patronage_history (
    id              BIGSERIAL PRIMARY KEY,
    month           TEXT NOT NULL,                          -- 'YYYY-MM' format, e.g. '2026-04'
    agent           TEXT NOT NULL,
    opening_total   INTEGER NOT NULL,                       -- frozen denominator (snapshot at month start)
    closing_active  INTEGER,                                -- end-of-month numerator (active debtors who bought)
    closing_pending INTEGER,                                -- 待激活 count at month end
    closing_rate    NUMERIC(5,2),                           -- closing_active / opening_total * 100, e.g. 57.83
    snapshot_date   DATE NOT NULL,                          -- when opening_total was captured
    archived_at     TIMESTAMPTZ,                            -- when closing values were archived (NULL = open month)
    notes           TEXT,                                    -- e.g. 'BACKFILL: reconstructed from 2026-04-30 file'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (month, agent)
);

CREATE INDEX IF NOT EXISTS idx_patronage_month ON patronage_history(month);
CREATE INDEX IF NOT EXISTS idx_patronage_agent ON patronage_history(agent);

-- updated_at trigger (uses existing set_updated_at() function from campaigns_schema.sql)
DROP TRIGGER IF EXISTS trg_patronage_updated_at ON patronage_history;
CREATE TRIGGER trg_patronage_updated_at
    BEFORE UPDATE ON patronage_history
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
