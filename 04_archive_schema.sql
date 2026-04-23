-- Miracle MD Dashboard — Agent Monthly Archive
-- Captures end-of-month results per agent for historical review

CREATE TABLE IF NOT EXISTS agent_monthly_archive (
  month TEXT NOT NULL,              -- "Apr 26"
  agent TEXT NOT NULL,              -- "BEN"

  -- Activity metrics
  total_ctn_paid NUMERIC DEFAULT 0,       -- Paid-basis CTN (commission-relevant)
  total_ctn_invoice NUMERIC DEFAULT 0,    -- Invoice-basis CTN
  active_debtors INTEGER DEFAULT 0,
  new_accounts INTEGER DEFAULT 0,

  -- Commission breakdown (RM, all paid-basis except brand)
  comm_normal NUMERIC DEFAULT 0,          -- T1/T2/GA/MA tier
  comm_brand NUMERIC DEFAULT 0,           -- Sum of all brand commissions (invoice-basis)
  comm_newbie_ctn NUMERIC DEFAULT 0,      -- Newbie CTN tier bonus
  comm_newbie_acc NUMERIC DEFAULT 0,      -- Newbie new-account bonus
  comm_campaigns NUMERIC DEFAULT 0,       -- Campaign claims approved
  comm_total NUMERIC DEFAULT 0,           -- Sum of all above

  -- KPI
  kpi1_score NUMERIC DEFAULT 0,           -- Main KPI score
  kpi2_score NUMERIC DEFAULT 0,           -- Secondary KPI (if applicable)
  kpi_details JSONB,                      -- Per-KPI-category hit details

  -- Brand detail (for deep dive)
  brand_performance JSONB,                -- {SUKUN: {pen: 5, ctn: 247, status: "none_hit", comm: 0}}

  -- Sales progression
  sales_tier TEXT,                        -- 'T1', 'T2', 'GA', 'MA', 'below_ma'
  sales_tier_ctn NUMERIC,                 -- CTN at which tier was hit

  -- Audit
  captured_at TIMESTAMPTZ DEFAULT NOW(),
  captured_method TEXT,                   -- 'auto_month_end' | 'manual' | 'recalc' | 'backfill'
  captured_by TEXT,

  PRIMARY KEY (month, agent)
);

CREATE INDEX IF NOT EXISTS idx_archive_month ON agent_monthly_archive(month);
CREATE INDEX IF NOT EXISTS idx_archive_agent ON agent_monthly_archive(agent);
