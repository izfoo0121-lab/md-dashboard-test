"""
cleanup_bad_claims.py v2 — batch-delete version (100x faster)
────────────────────────────────────────────────────────────────────
Removes claims for debtor-agent pairs where the debtor does NOT
actually belong to that agent (per Debtor Maintenance.xlsx).

v2 changes:
  - Batch DELETE (100 rows per request) instead of one-by-one
  - 9,662 claims: ~3-5 min instead of ~4 hours
  - --delete-camp-all flag to purge a specific camp entirely
    (use for test/accidental campaigns with no real data to preserve)
  - Per-camp summary table in preview

Usage:
  py -3.11 cleanup_bad_claims.py                              # Dry run (all camps)
  py -3.11 cleanup_bad_claims.py --commit                     # Actually delete
  py -3.11 cleanup_bad_claims.py --camp-pattern "bison"       # Filter to bison only
  py -3.11 cleanup_bad_claims.py --delete-camp-all camp_1775396958014 --commit
      # Purge camp_1775... entirely (all agents, no ownership check)

All changes logged to cleanup_log.txt for audit.
"""
import pandas as pd
import requests
import sys
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import re

SUPABASE_URL = 'https://rqitgmydcbyiygqjssrb.supabase.co'
SUPABASE_KEY = 'sb_publishable_8xb7ZaHyr3OF3WNEqufuDg_67spOIFw'
DEBTOR_FILE  = Path('Debtor Maintenance.xlsx')
BATCH_SIZE   = 100          # How many claims to delete per HTTP request

parser = argparse.ArgumentParser()
parser.add_argument('--month', default='Apr 26', help='Month label (e.g. "Apr 26")')
parser.add_argument('--commit', action='store_true', help='Actually delete (default: dry-run)')
parser.add_argument('--camp-pattern', default='.*', help='Regex for camp_ids to process (default: all camps)')
parser.add_argument('--delete-camp-all', action='append', default=[], help='Delete ALL claims for this camp_id (repeat for multiple). Use for test/accidental camps.')
parser.add_argument('--delete-orphans', action='store_true', help='Delete ALL claims where debtor_code is NOT in Debtor Maintenance (true orphans)')
args = parser.parse_args()


def log(msg):
    ts = datetime.now().strftime("[%H:%M:%S]")
    line = f"{ts} {msg}"
    print(line)
    with open('cleanup_log.txt', 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def fetch_claims_paginated(month):
    """Fetch ALL claims for the given month, paginating past Supabase's 1000-row cap."""
    all_rows = []
    offset = 0
    while True:
        url = f"{SUPABASE_URL}/rest/v1/claims?select=*&month=eq.{month.replace(' ', '%20')}"
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Range': f'{offset}-{offset + 999}'
        }
        r = requests.get(url, headers=headers)
        if not r.ok:
            log(f"  Fetch failed: {r.status_code} — {r.text[:200]}")
            break
        batch = r.json()
        if not batch:
            break
        all_rows.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
    return all_rows


def delete_batch(month, claims_to_delete):
    """Delete a batch of claims in one request using PostgREST `or()` filter.

    Each claim is uniquely identified by (month, agent, camp_id, debtor_code).
    We construct: or=(and(agent.eq.A,camp_id.eq.C,debtor_code.eq.D),and(...))
    """
    if not claims_to_delete:
        return 0, 0

    # Build an OR of ANDs filter
    conditions = []
    for c in claims_to_delete:
        # URL-encode special chars in values
        agent = requests.utils.quote(c['agent'], safe='')
        camp  = requests.utils.quote(c['camp_id'], safe='')
        code  = requests.utils.quote(c['debtor_code'], safe='')
        conditions.append(f"and(agent.eq.{agent},camp_id.eq.{camp},debtor_code.eq.{code})")

    or_filter = f"or=({','.join(conditions)})"
    url = f"{SUPABASE_URL}/rest/v1/claims?month=eq.{requests.utils.quote(month)}&{or_filter}"

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Prefer': 'return=minimal'
    }
    r = requests.delete(url, headers=headers)
    if r.ok:
        return len(claims_to_delete), 0
    else:
        log(f"  Batch delete failed ({r.status_code}): {r.text[:300]}")
        return 0, len(claims_to_delete)


def delete_whole_camp(month, camp_id):
    """Delete ALL claims for a specific camp_id. Use for test/accidental camps."""
    url = (
        f"{SUPABASE_URL}/rest/v1/claims"
        f"?month=eq.{requests.utils.quote(month)}"
        f"&camp_id=eq.{requests.utils.quote(camp_id)}"
    )
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Prefer': 'return=representation'  # Return deleted rows so we get a count
    }
    r = requests.delete(url, headers=headers)
    if r.ok:
        deleted_rows = r.json()
        return len(deleted_rows), 0
    else:
        log(f"  Whole-camp delete failed ({r.status_code}): {r.text[:300]}")
        return 0, -1


def main():
    log("=" * 60)
    log(f"Bad Claims Cleanup v2 — {'LIVE MODE' if args.commit else 'DRY RUN'}")
    log("=" * 60)
    log(f"  Month: {args.month}")
    log(f"  Camp filter: {args.camp_pattern}")
    if args.delete_camp_all:
        log(f"  PURGE ENTIRELY: {args.delete_camp_all}")
    log("")

    # ── Handle --delete-camp-all first (separate from normal cleanup) ──
    purge_targets = args.delete_camp_all
    purged_total = 0

    # ── Step 1: Load truth from Debtor Maintenance ──
    if not DEBTOR_FILE.exists():
        log(f"ERROR: {DEBTOR_FILE} not found. Aborting.")
        sys.exit(1)

    log(f"Step 1: Reading {DEBTOR_FILE}...")
    df = pd.read_excel(DEBTOR_FILE, dtype=str, engine='openpyxl')
    df.columns = [c.strip() for c in df.columns]
    truth = {}
    for _, row in df.iterrows():
        code  = str(row.get('Code', '')).strip()
        agent = str(row.get('Agent', '')).strip().upper()
        if code and agent and agent.lower() not in ('nan', 'none'):
            truth[code.upper()] = agent
    log(f"  Truth table: {len(truth):,} debtor->agent mappings")
    log("")

    # ── Step 2: Fetch all claims for month ──
    log(f"Step 2: Fetching {args.month} claims from Supabase...")
    claims = fetch_claims_paginated(args.month)
    log(f"  Retrieved {len(claims):,} claims total")
    log("")

    # ── Step 3: Partition ──
    # First: claims matching --delete-camp-all → purge entirely
    # Second: remaining claims matching --camp-pattern → ownership check
    pattern = re.compile(args.camp_pattern, re.IGNORECASE)

    to_purge = [c for c in claims if c.get('camp_id') in purge_targets]
    remaining = [c for c in claims if c.get('camp_id') not in purge_targets]

    # Apply camp-pattern filter + status=delivered filter to remaining
    filtered = [
        c for c in remaining
        if pattern.search(c.get('camp_id', '') or '')
           and c.get('status') == 'delivered'
    ]
    log(f"Step 3: Partitioned claims")
    log(f"  To purge entirely (camp_id in --delete-camp-all): {len(to_purge):,}")
    log(f"  To check ownership (camp-pattern + delivered):    {len(filtered):,}")
    log("")

    # ── Step 4: Identify bad claims ──
    log("Step 4: Identifying bad claims in filtered set...")
    bad_claims = []
    good_claims = []
    orphans = []
    for c in filtered:
        code  = (c.get('debtor_code') or '').upper()
        agent = (c.get('agent') or '').upper()
        true_owner = truth.get(code)
        if true_owner is None:
            orphans.append(c)
        elif true_owner == agent:
            good_claims.append(c)
        else:
            bad_claims.append(c)
    log(f"  Good (keep):    {len(good_claims):,}")
    log(f"  BAD (delete):   {len(bad_claims):,}")
    log(f"  Orphan (in DM miss): {len(orphans):,} — {'WILL DELETE' if args.delete_orphans else 'will keep'}")
    log("")

    # ── Step 5: Dedup good claims across camp_ids ──
    log("Step 5: Deduping good claims across camp_ids...")
    by_agent_debtor = defaultdict(list)
    for c in good_claims:
        key = (c['agent'], c['debtor_code'].upper())
        by_agent_debtor[key].append(c)

    extra_dupes = []
    dedup_good = []
    for group in by_agent_debtor.values():
        if len(group) == 1:
            dedup_good.append(group[0])
        else:
            group_sorted = sorted(group, key=lambda x: x.get('ts','') or '')
            dedup_good.append(group_sorted[0])
            extra_dupes.extend(group_sorted[1:])

    log(f"  After dedup: {len(dedup_good):,}")
    log(f"  Extra camp-id dupes: {len(extra_dupes):,}")
    log("")

    to_delete = bad_claims + extra_dupes
    if args.delete_orphans:
        to_delete = to_delete + orphans
        log(f"  Orphans added to delete queue: {len(orphans):,}")
        log("")

    # ── Step 6: Preview by camp_id ──
    log("Step 6: Delete summary by camp_id:")
    by_camp = defaultdict(lambda: {'bad':0, 'dupe':0, 'orphan':0})
    for c in bad_claims:
        by_camp[c['camp_id']]['bad'] += 1
    for c in extra_dupes:
        by_camp[c['camp_id']]['dupe'] += 1
    if args.delete_orphans:
        for c in orphans:
            by_camp[c['camp_id']]['orphan'] += 1
    for camp, counts in sorted(by_camp.items()):
        log(f"  {camp:30}: {counts['bad']:5} bad + {counts['dupe']:3} dupe + {counts['orphan']:3} orphan")
    log("")

    log(f"Total to delete (ownership): {len(to_delete):,}")
    log(f"Total to purge (camp-wide):  {len(to_purge):,}")
    log(f"GRAND TOTAL DELETIONS:       {len(to_delete) + len(to_purge):,}")
    log("")

    # ── Step 7: Execute or dry-run ──
    if not args.commit:
        log("DRY RUN — nothing deleted.")
        log("Run with --commit to actually delete.")
        return

    grand_total = len(to_delete) + len(to_purge)
    log(f"COMMIT MODE — deleting {grand_total:,} claims...")
    confirm = input(f"Type 'DELETE {grand_total}' to proceed: ")
    if confirm.strip() != f'DELETE {grand_total}':
        log("Aborted.")
        return

    # ── Step 8a: Purge whole camps first ──
    purged_success = 0
    purged_failed  = 0
    if to_purge:
        log("")
        log("Phase A: Purging whole camps...")
        for camp in purge_targets:
            log(f"  Purging {camp}...")
            n_ok, n_fail = delete_whole_camp(args.month, camp)
            purged_success += n_ok
            if n_fail != 0:
                purged_failed += 1
            log(f"    → {n_ok} rows deleted")

    # ── Step 8b: Batch-delete bad ownership claims ──
    log("")
    log(f"Phase B: Batch-deleting {len(to_delete):,} ownership-mismatch claims...")
    success = 0
    failed = 0
    batches = [to_delete[i:i+BATCH_SIZE] for i in range(0, len(to_delete), BATCH_SIZE)]
    for i, batch in enumerate(batches, 1):
        ok, fail = delete_batch(args.month, batch)
        success += ok
        failed += fail
        log(f"  Batch {i}/{len(batches)}: {ok} deleted, {fail} failed (running total: {success})")

    log("")
    log("=" * 60)
    log(f"PHASE A (whole-camp purge): {purged_success:,} deleted")
    log(f"PHASE B (ownership check):  {success:,} deleted, {failed:,} failed")
    log(f"TOTAL DELETED: {purged_success + success:,}")
    log(f"KEPT: {len(dedup_good):,} good + {len(orphans):,} orphans")
    log("=" * 60)


if __name__ == '__main__':
    main()
