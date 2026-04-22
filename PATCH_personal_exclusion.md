# Patch — Exclude P-Personal from Summary + Campaigns

## Business Rule (Isaac, 21 Apr 2026)

Personal-type debtors (P-Personal) should be:
- **Excluded** from summary counts (总户口, 已激活, 待激活, FLAGGED, 光顾率, 总新SKU)
- **Excluded** from all KPI calculations (already was for activation_rate, reactivation target, VIP target)
- **Excluded** from all campaigns (promo, FOC, festive, birthday, brand tiers)
- **Still visible** as cards in the debtor list below (agents can still interact with them)

## What Changed

### process_data.py (5 edits)

1. **Summary counts** (line 1143-1193): Personal filtered from active_count / pending_count / inactive_count / reactiv_count / total_debtors / total_new_sku — all now count non-Personal only.

2. **New fields exported**:
   - `total_debtors_all` — count INCLUDING Personal (reference only)
   - `personal_count` — how many Personal in the list
   - `exclusion_note` — "Summary counts exclude P-Personal"

3. **Campaigns blocked** for Personal (line 1105): If debtor is Personal, `campaigns = []`. No promo, FOC sample, festive, or birthday gift eligibility.

4. **Brand tiers blocked** for Personal (line 2427): `brand_camp_tiers` stays `{}` for Personal.

### sales_dashboard.html (3 edits)

1. **总户口 label** now reads: `总户口 (排除 Personal)` with small muted suffix
2. **光顾率 label** — removed asterisk (was explaining Personal exclusion; now the footnote covers all counts)
3. **Footnote updated**: `* 所有数目排除 P-Personal · All counts exclude P-Personal (still shown in list below)`
4. **Flag count** now excludes Personal-type debtors from the FLAGGED summary box

## Expected Behavior After Deploy

For each agent:
- 总户口 drops by however many Personal accounts they have
- 已激活 / 待激活 / 光顾率 / 总新SKU all shrink proportionally
- Personal cards STILL appear in the scrollable list below (with their Personal badge)
- Tapping a Personal card shows the card as normal, but Camps tab shows no campaigns for them
- Flagging a Personal debtor: flag saves, but doesn't increment the FLAGGED count

## Stacking With Previous Patches

This stacks correctly with:
- Active=Unchecked filter: closed accounts REMOVED from list entirely
- Archived agent filter: JW excluded from per-agent views but counted in team totals

Final rule for what appears in agent's debtor list:
  **DM Active=Checked** (hard filter)
  ∪ (union)
  **Transactions exist** (fallback, also Active=Checked only)

Final rule for summary counts:
  **DM Active=Checked AND NOT Personal**

