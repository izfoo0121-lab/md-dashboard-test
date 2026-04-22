# Patch — 前月条数 Correct Definition

## Business Rule

**前月条数 (已付款)** = Invoices dated in any of the **3 months BEFORE cur_month**, paid **in cur_month**.

For April 2026: invoiced in Jan/Feb/Mar 2026, paid in April 2026.
For May 2026: invoiced in Feb/Mar/Apr 2026, paid in May 2026.

## What Was Wrong

Old code: `canggih[paid_on == prev_m]["qty_ctn"].sum()`

That calculates "CTN paid IN March" (regardless of when invoiced). Completely different metric from what Isaac wants.

## What's Fixed

1. `_calc_prev_month_ctn()` now filters: `tranx_mth.isin(prev_3_months) & paid_on == cur_month`
2. New function `_calc_cur_month_invoiced_paid()`: `tranx_mth == cur_month & paid_on == cur_month`
3. Dashboard math: 前月 + 本月 = 总共 (disjoint sets, no double counting)

## Expected Numbers After Deploy

Your current dashboard shows:
- 前月条数: 78,081.55  ← WRONG (this was "all March payments")
- 本月条数: 43,915
- 总共:    121,996.55

After fix, expect roughly:
- 前月条数: ~5,000-15,000 (Jan+Feb+Mar invoices that rolled into Apr)
- 本月条数: ~35,000-40,000 (Apr invoices paid in Apr)
- 总共:    ~40,000-50,000 (total Canggih paid in Apr = what was team_canggih_ctn)

If you want to verify manually:
- AutoCount → MD Sales Report → filter paid_on = "Apr 26"
- Of those, filter tranx_mth in ("Jan 26", "Feb 26", "Mar 26") → this is the new 前月条数
- Of those, filter tranx_mth = "Apr 26" → this is the new 本月条数

