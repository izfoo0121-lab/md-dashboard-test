# Patch — Filter Active=Unchecked Debtors

## Business Rule

From Debtor Maintenance, debtors with **Active = Unchecked** are "closed accounts" and should NOT appear in any agent-facing view:
- 总户口 count (drops from 225 → 139 per Isaac's handoff doc)
- Debtor cards list
- Camps tab
- KPI calculations (activation rate, reactivation, etc.)
- Birthday campaign pool (drops from 130 → 73)

Revenue totals at team/group level (calc_group_brand_targets) are NOT affected because actual CTN sold is still real revenue, even to now-closed accounts.

## What Was Wrong

Previous `load_debtors()` / `calc_debtor_cards()` code read Company Name, Agent, Type, etc. but NEVER looked at the Active column. Every debtor in the DM file (regardless of status) was loaded.

## What's Fixed

4 surgical changes in process_data.py:

1. **ACTIVE_COL detection** — auto-find the "Active" column in Debtor Maintenance
2. **dm_active flag** — parse the Checked/Unchecked value, store as boolean per debtor
3. **Primary debtor list filter** — only include debtors where `dm_active == True`
4. **TX fallback respects Active flag** — a stray April invoice from a closed debtor doesn't resurrect them

All changes are backwards-compatible: if ACTIVE_COL is absent, dm_active defaults to True and behavior is identical to before the patch.

## Expected Numbers After Deploy

Per Isaac's handoff doc:
- BEN: 225 → 139 debtors (86 closed accounts removed)
- Birthday pool (April): 130 → 73
- 总户口 for every agent drops by however many closed accounts they had

## Verification

After running `update_dashboard.bat "Apr 26"`, look in console for lines like:
```
  BEN: 12 debtors excluded (Active=Unchecked)
  CJ: 8 debtors excluded (Active=Unchecked)
```

If no such lines appear for any agent → the Active column wasn't detected. Debug:
```python
# Check your Debtor Maintenance.xlsx — what's the exact column header?
# Must be exactly "Active" (case-insensitive, trimmed)
```

If headers are like "Is Active" or "Status" or "活跃", edit line 868 of process_data.py:
```python
ACTIVE_COL = next((c for c in cols if c.strip() == 'Active'), None)
# Change 'Active' to your actual header name.
```

