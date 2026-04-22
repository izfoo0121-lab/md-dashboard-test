# Patch — KPI Manual Entry for new_accounts, vip_count, birthday_campaign

## Changes Summary

| KPI Item | Before | After |
|----------|--------|-------|
| 开户口 (new_accounts) | auto-counted from debtor_cards | Admin enters via admin.html → Supabase kpi_manual |
| VIP 招聘 (vip_count) | auto-counted from `vip=true` debtors | Admin enters via admin.html → Supabase kpi_manual |
| 生日礼物 Campaign | Agent enters manually in KPI tab | Auto-counted from Supabase claims + audit_log (VERIFIED only) |
| **Total Score** | Reflected wrong actuals | Recomputed from above + existing fields |

## Deployment Order (CRITICAL)

### Step 1 — Create Supabase table
Run `02_supabase_kpi_manual_schema.sql` in the Supabase SQL editor. Creates `kpi_manual` table.

Verify with:
```sql
select count(*) from kpi_manual;  -- should return 0
```

### Step 2 — Replace 3 files locally
Overwrite in `C:\Users\tgy_3\Desktop\md-dashboard\`:
- `process_data.py`
- `sales_dashboard.html`
- `admin.html`

### Step 3 — Enter initial KPI Manual values (ADMIN)
Open `admin.html` → enter password → click **📊 KPI Manual** tab.
- Select month "Apr 26"
- Enter 新户口 + VIP招聘 for each agent (verified actuals)
- Click **💾 SAVE ALL TO SUPABASE**

### Step 4 — Run bat (regenerates dashboard_data.json with new structure)
```powershell
update_dashboard.bat "Apr 26"
```

Console should show birthday_campaign has `input_role:none` / `source:auto_claims` in the exported JSON.

### Step 5 — Push
```powershell
git add sales_dashboard.html admin.html
git commit -m "KPI manual entry: new_accounts, vip_count via Supabase; birthday auto-counted"
git push origin main
```

### Step 6 — Test on phone
```
https://izfoo0121-lab.github.io/md-dashboard/sales_dashboard.html?v=kpi1
```

Login as agent → KPI tab:
- 新户口: shows admin-entered value (not auto)
- VIP 招聘: shows admin-entered value (not auto)
- 生日礼物: shows "X verified / Y submitted · N pending" (read-only, no edit button)
- Total Score: reflects the updated values

## Data Flow Post-Deploy

```
ADMIN ENTERS                  AGENT CLICKS              AGENT VIEWS KPI
     │                              │                          │
     ▼                              ▼                          │
admin.html                   sales_dashboard                   ▼
KPI Manual tab               Camps tab                 applyKPIOverrides()
     │                        (Delivered button)        │
     ▼                              │                   │
┌─────────────┐              ┌─────────────┐            │
│ kpi_manual  │              │ claims      │            │
│ (Supabase)  │              │ (Supabase)  │            │
└─────────────┘              └─────────────┘            │
     │                              │                   │
     │                       ADMIN AUDITS               │
     │                      campaign_audit.html         │
     │                              │                   │
     │                              ▼                   │
     │                       ┌─────────────┐            │
     │                       │ audit_log   │            │
     │                       │ (Supabase)  │            │
     │                       └─────────────┘            │
     │                              │                   │
     ▼                              ▼                   │
All three read by dashboard ──────────────────────────┘
```

## Birthday Camp IDs Matched

Dashboard counts claims where `camp_id` contains either:
- `"birthday"` (case-insensitive)
- `"bday"` (case-insensitive)

This catches ALL variants:
- `birthday_gift_auto` (process_data.py-generated)
- `camp_birthday_apr26` (admin-created)
- `camp_bday_apr26` (seen in your data)
- Any future variant

## Scoring Logic (Birthday KPI Example)

Given:
- Agent has 10 birthday targets (pool)
- Agent clicked Delivered on 8 → creates 8 claims with status='delivered'
- Admin verified 6, rejected 1, pending 1

Dashboard display:
- actual (score): **6** (verified only)
- submitted: **7** (8 minus 1 rejected)
- pending: **1**
- Sub text: "6 verified / 7 submitted · Target 10 · 1 pending"
- Score calc: min(6/10, 1.0) × weight × 100 = 60% × 1% = 0.60 pts

## Troubleshooting

### "新户口 still shows auto-count after update"
- Browser cache. Use `?v=kpi2` instead of `?v=kpi1`.
- Check console for `[KPI] kpi_manual fetch failed` — means Supabase table missing.

### "Birthday shows 0 verified / 0 submitted"
- No claims yet in Supabase for this month. Agent needs to click Delivered in Camps tab.
- Or: all claims rejected in audit. Check campaign_audit.html.

### "Total Score still wrong"
- applyKPIOverrides runs async. If you see old values briefly, that's just the overrides loading.
- Refresh the KPI tab (switch away and back).

### "Admin KPI Manual tab shows no agents"
- CONFIG.agents is empty or not loaded. Go to Agent Targets tab first — that loads CONFIG.

