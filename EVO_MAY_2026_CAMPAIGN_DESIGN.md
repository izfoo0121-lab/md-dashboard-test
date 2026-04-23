# EVO May 2026 Campaign — Design Document

**Status**: Design locked (April 22, 2026) — ready for implementation
**Owner**: Isaac (GRP 2A MD)
**Target launch**: May 1, 2026 (9 days from this doc)
**Last updated**: April 22, 2026 — brainstorming session

---

## 🎯 Campaign Objective

Grow EVO shop penetration from 28.7% → ≥40% across all groups by end of May 2026.

**Strategy**: Convert 2,359 existing non-EVO shops (across 47 agents in 6 groups) to first-time EVO buyers, incentivized via tiered commission + FOC welcome gift.

**Mechanism**: Replace normal EVO brand commission for May only with a new gate (# of new shops activated).

---

## 📋 Core Business Rules (LOCKED)

### Rule 1 — Qualifying Shop Definition

A debtor **QUALIFIES** for EVO May campaign if ALL conditions are met:

| Condition | Detail |
|-----------|--------|
| Active status | Active = Checked in Debtor Maintenance |
| Type | SH-Shop (non-Personal, non-empty type) |
| No prior EVO | No EVO invoice in Feb/Mar/Apr 2026 |
| Bought in May | Has EVO invoice dated in May 2026 (invoice-basis) |

**Note**: Lapse window is **Feb-Apr 2026** (3-month rolling), NOT Jan-Mar as originally stated in memo. Memo stays — Isaac will clarify in agent briefing.

### Rule 2 — Qualifying Shop Pool Sources

Two sources merge into one qualifying pool:

1. **Pre-list (static)**: 2,359 pre-identified non-EVO shops (from Jan-Mar baseline)
2. **New accounts (dynamic)**: Debtors with `open_date` in May 2026, no prior EVO purchase

Both pools qualify under same rules. Pre-list = planning tool, not gate.

### Rule 3 — Tier Structure

Tier determined by **# of INVOICED qualifying shops** activated during May:

| Tier | Shops Required | New Acct Ctns Rate | Existing Customer Ctns Rate |
|------|----------------|---------------------|------------------------------|
| No Tier | < 4 | RM 0 | RM 0 |
| **Baseline** | 4-6 | RM 1.80/ctn | RM 1.80/ctn |
| **Tier 1** | 7-9 | RM 2.80/ctn | RM 1.80/ctn |
| **Tier 2** | 10-13 | RM 3.80/ctn | RM 1.80/ctn |
| **Tier 3** | 14+ | RM 4.80/ctn | RM 1.80/ctn |

**Jump-tier logic**: Once threshold hit, ALL new account ctns earn at that tier's rate (not graduated).

**Existing customer commission**: RM 1.80/ctn regardless of tier (unchanged from normal brand commission rate).

### Rule 4 — Commission Payout Basis

- Only **PAID** ctns count for commission (paid_on date = May or June 2026)
- 2-month collection window
- Unpaid invoices at June 30 = excluded from payout
- Reconciliation: early July 2026

### Rule 5 — Tier Counting Basis (Dashboard UX)

- During May: tier counted from **INVOICED** shops (motivational, updates daily)
- End of June: tier re-confirmed based on **PAID** shops (reality check)
- Any discrepancy: final payout uses PAID version

### Rule 6 — FOC Mechanism

- 5 packs CM/CMX/CMP given FREE on qualifying shop's first EVO order
- **One-time per debtor code** (tracked)
- Cost: RM 17.75/shop (borne by company)
- Bearer: Company (part of acquisition cost)

### Rule 7 — Interaction With Normal Brand Commission

**For May 2026 only**:
- Normal EVO brand commission (penetration target + CTN target gate) = **SUSPENDED**
- Campaign replaces normal EVO commission entirely
- Other brand commissions (SUKUN, iFACE, BISON, TR20, LAM+LWM) = unchanged

---

## 🔢 Worked Examples

### Example A — Steady Performer (Baseline)
Agent KI-MI activates 5 shops. Each buys ~3 ctn. Plus existing customers.
- New account ctns: 15 (5 × 3)
- Existing customer ctns: 40
- Tier: **Baseline**
- Commission: (15 × RM 1.80) + (40 × RM 1.80) = **RM 99.00**

### Example B — Strong Performer (Tier 2)
Agent KI-MI activates 12 shops. 36 new account ctns + 40 existing.
- Tier: **Tier 2**
- Commission: (36 × RM 3.80) + (40 × RM 1.80) = **RM 208.80**

### Example C — Underperformer (No Tier)
Agent KI-MI only activates 3 shops. 6 new acct ctns + 40 existing.
- Tier: **None**
- Commission: **RM 0** (even with 40 existing ctns sold — harsh but intentional)

---

## 🖥️ Dashboard Design (Draft)

### Agent Sales Dashboard — EVO May Campaign Card

```
┌────────────────────────────────────────────┐
│ 🎯 EVO MAY 2026 CAMPAIGN                   │
│                                              │
│ NEW SHOPS ACTIVATED (invoiced)              │
│ ▰▰▰▰▰▰▱▱▱▱▱ 6 / 7 → next tier              │
│                                              │
│ Current tier: BASELINE ✓                    │
│ Next tier: TIER 1 at 7 shops (+1 more)      │
│                                              │
│ ─────────────────────────────────           │
│                                              │
│ 💰 PROJECTED COMMISSION (May + Jun paid)    │
│                                              │
│ New acct ctns (invoiced): 18                │
│ Existing customer ctns: 55                  │
│ Current rate: RM 1.80 (Baseline)            │
│                                              │
│ Projected: RM 131.40                        │
│                                              │
│ ⚠️ Commission confirmed end of June          │
│    based on PAID ctns only                  │
│                                              │
│ ─────────────────────────────────           │
│                                              │
│ 🏪 ACTIVATED SHOPS (6)                      │
│ ⭐ KEDAI ABC      3 ctn  PAID   RM 5.40    │
│ ⭐ NEW SHOP 1     5 ctn  PENDING RM 9.00   │
│ ⭐ KEDAI XYZ      2 ctn  PAID   RM 3.60    │
│ ⭐ ... (3 more)                             │
│                                              │
│ [View Full Target List (165)]              │
└────────────────────────────────────────────┘
```

### Dashboard Design Principles
- Dual progress: **shops activated** (primary) + **ctns earned** (secondary)
- "Need X more shops to Tier 1" motivational message
- Transparent shop list (PAID/PENDING status)
- Target list accessible but not intrusive
- PAID vs PENDING status clearly labeled

### Admin View (campaign_audit.html)
- Pre-campaign: upload target list per agent
- During May: monitor activations per agent
- Manual override flag: `campaign_exclude` on specific debtor (edge cases)
- End of May: review projected tier hits
- End of June: finalize based on paid invoices
- Export reconciliation report

---

## 📅 Timeline

| Date | Action | Owner |
|------|--------|-------|
| 25-30 Apr | Agent briefing + target list distribution | Isaac |
| 28 Apr | Memo correction: clarify Feb-Apr window | Isaac (verbal/Telegram) |
| 1 May | Campaign launch | System |
| Daily in May | Bat run → updates invoiced counts | System auto |
| Weekly in May | Isaac sends tier status to each agent | Isaac |
| 31 May | Last day for activation invoices | System |
| May-Jun | Collection window | Agents |
| 30 Jun | Collection window closes | System |
| 1-5 Jul | Reconciliation: recount based on PAID | Isaac + Accounts |
| 12 Jul | Commission payout | Accounts |

---

## 🏗️ Technical Implementation Plan

### Database Schema (Supabase)

```sql
-- Campaign table (extends existing pattern)
CREATE TABLE evo_may_2026_campaign (
  id SERIAL PRIMARY KEY,
  campaign_id TEXT DEFAULT 'evo_may_2026',
  start_date DATE DEFAULT '2026-05-01',
  end_date DATE DEFAULT '2026-05-31',
  collection_end DATE DEFAULT '2026-06-30',
  status TEXT DEFAULT 'active',
  rules_version TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Per-agent config (tier thresholds, should be same for all)
CREATE TABLE evo_campaign_tiers (
  tier_name TEXT PRIMARY KEY,
  shops_required INTEGER,
  rate_new_acct NUMERIC,
  rate_existing NUMERIC
);
-- Pre-populated with Baseline/T1/T2/T3 rows

-- Pre-uploaded target shops (optional, for visibility only)
CREATE TABLE evo_campaign_targets (
  debtor_code TEXT PRIMARY KEY,
  agent TEXT,
  group_name TEXT,
  added_to_list_at TIMESTAMPTZ DEFAULT NOW()
);

-- Admin override flags (edge cases)
CREATE TABLE evo_campaign_overrides (
  debtor_code TEXT PRIMARY KEY,
  action TEXT,  -- 'include' | 'exclude'
  reason TEXT,
  overridden_by TEXT,
  overridden_at TIMESTAMPTZ DEFAULT NOW()
);

-- FOC tracking (one-time per shop)
CREATE TABLE evo_campaign_foc (
  debtor_code TEXT PRIMARY KEY,
  agent TEXT,
  first_evo_invoice_date DATE,
  foc_issued BOOLEAN DEFAULT false,
  foc_issued_at TIMESTAMPTZ,
  foc_issued_by TEXT
);

-- Per-agent results (computed, stored for reporting)
CREATE TABLE evo_campaign_results (
  agent TEXT PRIMARY KEY,
  snapshot_basis TEXT,  -- 'invoiced' | 'paid'
  snapshot_date TIMESTAMPTZ,
  shops_activated INTEGER,
  tier TEXT,
  new_acct_ctns NUMERIC,
  existing_ctns NUMERIC,
  commission_new_acct NUMERIC,
  commission_existing NUMERIC,
  commission_total NUMERIC
);
```

### process_data.py Changes

1. **Add campaign qualification calculator**:
   - Input: agent, month, sales_df, debtor_info
   - For each agent, find qualifying shops (Feb-Apr no EVO + May bought EVO)
   - Count invoiced qualifying shops → determine tier
   - Sum new acct ctns + existing ctns (paid_on in May/Jun)
   - Compute commission

2. **Output to dashboard_data.json**:
   - `agents[X].evo_may_campaign` object with all tier/commission data

3. **Auto-archive at end**:
   - When June ends, snapshot final PAID-based results to `agent_monthly_archive`
   - Tag with `evo_may_2026_final` marker

### admin.html Changes

- New tab: "📢 EVO May Campaign"
- Upload target list (bulk CSV/Excel import)
- View/edit admin overrides per debtor
- Monitor campaign progress per agent
- Manual "Recalculate" button
- Export reconciliation report (for accounts team)

### sales_dashboard.html Changes

- New campaign card per agent (EVO May specific)
- Dual progress bar (shops + ctns)
- "Next tier" motivational message
- Shop list with PAID/PENDING status

---

## ⚠️ Edge Cases Documented

### Edge Case 1: Cross-Agent Shop Purchase
**Scenario**: Shop on Agent A's target list → Agent B somehow invoices EVO to that shop in May.
**Rule**: Credit goes to whoever's agent code is on the invoice (actual seller), not list owner.

### Edge Case 2: Returning Lapsed Buyer
**Scenario**: Shop bought EVO in January 2026, nothing since. Buys EVO May 2026.
**Rule**: Feb-Apr lapse window satisfied → **qualifies** (despite Jan 2026 purchase).

### Edge Case 3: Shop Opens In May + Buys EVO Same Day
**Scenario**: New account opened May 5, buys EVO May 5.
**Rule**: Automatically qualifies (no Feb-Apr history + May purchase).

### Edge Case 4: Invoice Dated April, Paid May
**Scenario**: Invoice 30 Apr, paid 5 May. Is this May campaign activity?
**Rule**: Invoice-basis for tier counting uses INVOICE DATE (April) → NOT qualifying. Collection-basis uses PAID date but only with qualifying shops. → **Does not qualify**.

### Edge Case 5: Invoice May, Paid July
**Scenario**: Invoice 28 May (qualifying), paid 15 July (after collection window).
**Rule**: Shop activated (tier count OK), but commission NOT paid (outside May-Jun paid window). Agent sees projection during May, reality in July (zero).

### Edge Case 6: Shop On List But Buys In Last Week Of April
**Scenario**: Pre-list shop, buys EVO April 28, continues in May.
**Rule**: Shop now has EVO history in Apr → lapse window broken → **NOT qualifying** for May campaign. (Agent essentially "lost" the opportunity.)

---

## 📊 Success Metrics

### Primary KPIs (end of June 2026)
- Total new EVO shops activated (paid basis)
- EVO penetration % at end of May
- Agent-level tier distribution (how many hit each tier)
- Total commission paid out
- Total FOC cost

### Secondary Indicators
- Ratio of pre-list activations vs new account activations
- Average ctns per new shop
- Paid-to-invoiced ratio (collection performance)

### Archive After June
- Snapshot all data to `agent_monthly_archive`
- Tag with `campaign=evo_may_2026`
- Reusable for:
  - Reviewing agent performance
  - Designing future campaigns
  - Reconciliation disputes

---

## ❓ Open Questions (Parked For Next Session)

1. **FOC tracking mechanism**: Who logs FOC issuance? Auto from invoice data, or manual admin entry?
2. **Admin override UI**: Where in admin.html does edge-case handling live?
3. **Campaign setup form**: How does Isaac configure this campaign in admin? Reuse existing campaign pattern or new form?
4. **Briefing document**: Separate doc for agents explaining rules in simple language?
5. **Performance dashboard for Isaac**: Team-wide view of campaign progress?

---

## 🎭 Business Concerns To Monitor

### Concern 1: Agent Who Can't Find 4 Shops
Agents in groups with already-high EVO penetration may struggle to find 4 qualifying shops. 
**Mitigation**: Their pre-list might be small, but they can still open new accounts in May.

### Concern 2: Pre-Invoice/Post-Paid Mismatch
Agent sees "6 shops activated" in May, but by July only 4 have actually paid.
**Mitigation**: Clear UX warning about projection vs confirmed. Weekly status updates from Isaac.

### Concern 3: Existing Customer Ctn Drop
Agents may neglect existing customers while hunting new. Existing EVO ctns could drop in May.
**Monitoring**: Track week-over-week existing customer ctn volume.

### Concern 4: FOC Cost Overrun
If campaign overperforms (e.g., 500 shops activated), FOC cost = RM 8,875 (above planning).
**Already provisioned**: Memo's max FOC projection is RM 41,872 across all groups.

---

## 📝 Session Notes (April 22, 2026 Brainstorm)

### Key Decisions Made
- Qualification: Feb-Apr no EVO + May bought (corrected from memo's Jan-Mar)
- Tier: Jump logic on shop count (not CTN volume)
- Tier counting: INVOICED basis during month
- Commission: PAID basis for final payout
- Stacking: New acct at tier rate + existing at RM 1.80 flat
- Replacement: Campaign replaces normal EVO commission for May
- Pre-list: Planning tool only, not gate

### What We Avoided
- Over-engineering (considered graduated tiers, rejected)
- Multiple campaigns (considered 2 separate, rejected for agent UX)
- Fully dynamic qualification with no pre-list (rejected — pre-list useful for agent focus)

### Deferred To Implementation Session
- FOC tracking mechanics
- Admin override UI details
- Agent dashboard CSS/styling
- Campaign archive integration
- Performance monitoring for Isaac

---

## 🚀 Next Session Actions

1. Review this design doc
2. Finalize FOC tracking + admin override UX
3. Design agent dashboard mockup in detail
4. Build campaign-specific Supabase tables
5. Update process_data.py to calculate campaign
6. Update admin.html for campaign config + monitoring
7. Update sales_dashboard.html for agent view
8. Pre-load 2,359 target list
9. Launch testing (end of April)
10. Launch production (May 1)

**Estimated implementation time**: 5-7 hours (spread across 2-3 focused sessions)

---

*End of design doc. Save this file as `C:\Users\tgy_3\Desktop\md-dashboard\EVO_MAY_2026_CAMPAIGN_DESIGN.md` for reference.*
