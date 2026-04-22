#!/usr/bin/env python3
"""
MIRACLE-奇迹 MD Dashboard — One-time Gist → Supabase migration

What this does:
  1. Reads your existing GitHub Gist (old backend) using any still-valid token
     (if all are dead, reads from local cached JSON files instead).
  2. Imports claims, flags, and KPI scores into Supabase tables.
  3. Logs a summary row to audit_log.

Usage:
  py -3.11 migrate_gist_to_supabase.py

Prerequisites:
  pip install requests

Configuration:
  Edit the CONFIG section below. If GIST_TOKEN is None, script will try to
  load from local files (dashboard_data.json, gist_config.json).
"""

import json
import sys
import os
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed.")
    print("Run: pip install requests --break-system-packages")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════
# CONFIG — edit if needed
# ═══════════════════════════════════════════════════════════════════════

SUPABASE_URL = 'https://rqitgmydcbyiygqjssrb.supabase.co'

# Publishable key — safe to embed (matches HTML files). Enough permission for inserts.
SUPABASE_KEY = 'sb_publishable_8xb7ZaHyr3OF3WNEqufuDg_67spOIFw'

# The Gist to read from. Leave GIST_TOKEN as None to fall back to local JSON files.
GIST_ID    = 'ceb4064c9e2a6d37c6e52c3b02f04a1d'
GIST_TOKEN = None   # put a working gist-scope token here if you still have one; else None

# Months to migrate (in Gist slug format — no space)
MONTHS_TO_MIGRATE = [
    ('Apr 26', 'Apr26'),
    ('Mar 26', 'Mar26'),
]

# Dashboard folder — where your HTML + JSON files live
DASHBOARD_DIR = Path(r'C:\Users\tgy_3\Desktop\md-dashboard')

# ═══════════════════════════════════════════════════════════════════════


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


# ── Supabase helpers ────────────────────────────────────────────────────

def sb_headers(prefer=None):
    h = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
    }
    if prefer:
        h['Prefer'] = prefer
    return h


def sb_upsert(table, rows, conflict_cols):
    """Upsert rows into a Supabase table via PostgREST."""
    if not rows:
        return 0
    url = f'{SUPABASE_URL}/rest/v1/{table}?on_conflict={conflict_cols}'
    # Batch in chunks of 500 to avoid request-size limits
    inserted = 0
    for i in range(0, len(rows), 500):
        chunk = rows[i:i+500]
        r = requests.post(
            url,
            headers=sb_headers('resolution=merge-duplicates,return=minimal'),
            json=chunk,
            timeout=30,
        )
        if r.status_code >= 400:
            log(f"  ERROR upserting to {table}: HTTP {r.status_code} — {r.text[:200]}")
            return inserted
        inserted += len(chunk)
    return inserted


# ── Gist reader ─────────────────────────────────────────────────────────

def fetch_gist(gist_id, token):
    """Fetch all files in a Gist. Returns dict of filename → parsed JSON."""
    if not token:
        return None
    r = requests.get(
        f'https://api.github.com/gists/{gist_id}',
        headers={'Authorization': f'Bearer {token}',
                 'Accept': 'application/vnd.github+json'},
        timeout=20,
    )
    if r.status_code == 401:
        log("  Gist token rejected (401 Bad credentials) — falling back to local files")
        return None
    if not r.ok:
        log(f"  Gist fetch failed: HTTP {r.status_code}")
        return None
    data = r.json()
    out = {}
    for fname, fobj in (data.get('files') or {}).items():
        key = fname.replace('.json', '')
        try:
            out[key] = json.loads(fobj.get('content') or '{}')
        except json.JSONDecodeError:
            out[key] = {}
    log(f"  ✓ Fetched {len(out)} files from Gist")
    return out


# ── Local fallback reader ──────────────────────────────────────────────

def fetch_local_cache():
    """Read data from local dashboard files (fallback when Gist token is dead)."""
    out = {}

    # Try dashboard_data.json (contains everything baked in)
    dd_path = DASHBOARD_DIR / 'dashboard_data.json'
    if dd_path.exists():
        try:
            with open(dd_path, encoding='utf-8') as f:
                dd = json.load(f)
            # Extract gist-shaped data if present
            if 'gist_cache' in dd:
                out.update(dd['gist_cache'])
                log(f"  ✓ Loaded {len(dd['gist_cache'])} buckets from dashboard_data.json")
        except Exception as e:
            log(f"  ! Could not read dashboard_data.json: {e}")

    # Also try any monthly snapshot JSONs (data_apr26.json etc.)
    for snap in DASHBOARD_DIR.glob('data_*.json'):
        try:
            with open(snap, encoding='utf-8') as f:
                s = json.load(f)
            if 'gist_cache' in s:
                for k, v in s['gist_cache'].items():
                    # Merge (preferring latest by filename date — crude but fine)
                    if k not in out or not out[k]:
                        out[k] = v
        except Exception:
            pass

    return out


# ── Parsing helpers ────────────────────────────────────────────────────

def claims_to_rows(month, claims_obj):
    """claims_obj = { '{agent}_{campId}_{debtorCode}': {ts, remark, bulk, ...}, ... }
    Returns list of Supabase rows.
    """
    rows = []
    for comp_key, val in (claims_obj or {}).items():
        if not isinstance(val, dict):
            continue
        parts = comp_key.split('_')
        if len(parts) < 3:
            continue
        agent = parts[0]
        debtor_code = parts[-1]
        camp_id = '_'.join(parts[1:-1])
        rows.append({
            'month'      : month,
            'agent'      : agent,
            'camp_id'    : camp_id,
            'debtor_code': debtor_code,
            'status'     : val.get('status', 'delivered'),
            'remark'     : val.get('remark', '') or '',
            'bulk'       : bool(val.get('bulk', False)),
            'actor'      : val.get('actor', 'migration'),
            'ts'         : val.get('ts') or None,
        })
    return rows


def flags_to_rows(month, flags_obj):
    """flags_obj = { 'AGENT': { 'debtorCode': {reason, ts}, ... }, ... }"""
    rows = []
    for agent, agent_flags in (flags_obj or {}).items():
        for debtor_code, v in (agent_flags or {}).items():
            if isinstance(v, dict):
                rows.append({
                    'month'      : month,
                    'agent'      : agent,
                    'debtor_code': debtor_code,
                    'reason'     : v.get('reason', '') or '',
                    'ts'         : v.get('ts') or None,
                })
            else:
                # Legacy: flag was just a truthy value
                rows.append({
                    'month'      : month,
                    'agent'      : agent,
                    'debtor_code': debtor_code,
                    'reason'     : '',
                })
    return rows


def kpi_to_rows(kpi_obj):
    """kpi_obj = { 'Apr 26': {'BEN': {...}, 'CJ': {...}}, ... }"""
    rows = []
    for month, by_agent in (kpi_obj or {}).items():
        for agent, scores in (by_agent or {}).items():
            rows.append({
                'month' : month,
                'agent' : agent,
                'scores': scores or {},
            })
    return rows


# ── Main migration ─────────────────────────────────────────────────────

def main():
    log("═══════════════════════════════════════════════════════════")
    log("  Gist → Supabase Migration")
    log("═══════════════════════════════════════════════════════════")
    log(f"  Supabase URL: {SUPABASE_URL}")
    log(f"  Dashboard dir: {DASHBOARD_DIR}")
    log("")

    # Step 1: Fetch source data
    log("▶ Step 1: Fetching source data…")
    data = None
    if GIST_TOKEN:
        log(f"  Trying Gist {GIST_ID} with provided token…")
        data = fetch_gist(GIST_ID, GIST_TOKEN)

    if not data:
        log("  Falling back to local JSON files…")
        data = fetch_local_cache()

    if not data:
        log("  ✗ No data found in Gist or local files. Aborting.")
        sys.exit(1)

    log(f"  Available buckets: {sorted(data.keys())}")
    log("")

    # Step 2: Verify Supabase connection
    log("▶ Step 2: Verifying Supabase connection…")
    r = requests.get(
        f'{SUPABASE_URL}/rest/v1/claims?select=count',
        headers={'apikey': SUPABASE_KEY, 'Prefer': 'count=exact'},
        timeout=10,
    )
    if r.status_code == 200:
        log(f"  ✓ Supabase reachable (existing claims row count visible)")
    else:
        log(f"  ✗ Supabase error: HTTP {r.status_code} — {r.text[:200]}")
        sys.exit(1)
    log("")

    # Step 3: Migrate claims for each month
    log("▶ Step 3: Migrating claims…")
    total_claims = 0
    for month_label, month_slug in MONTHS_TO_MIGRATE:
        bucket = f'claims_{month_slug}'
        claims_obj = data.get(bucket, {})
        rows = claims_to_rows(month_label, claims_obj)
        if not rows:
            log(f"  {month_label}: no claims found in bucket '{bucket}' — skipping")
            continue
        n = sb_upsert('claims', rows, 'month,agent,camp_id,debtor_code')
        total_claims += n
        log(f"  ✓ {month_label}: upserted {n}/{len(rows)} claims")
    log("")

    # Step 4: Migrate flags for each month
    log("▶ Step 4: Migrating flags…")
    total_flags = 0
    for month_label, month_slug in MONTHS_TO_MIGRATE:
        bucket = f'flags_{month_slug}'
        flags_obj = data.get(bucket, {})
        rows = flags_to_rows(month_label, flags_obj)
        if not rows:
            log(f"  {month_label}: no flags found in bucket '{bucket}' — skipping")
            continue
        n = sb_upsert('flags', rows, 'month,agent,debtor_code')
        total_flags += n
        log(f"  ✓ {month_label}: upserted {n}/{len(rows)} flags")
    log("")

    # Step 5: Migrate KPI scores
    log("▶ Step 5: Migrating KPI scores…")
    kpi_obj = data.get('kpi_scores', {})
    rows = kpi_to_rows(kpi_obj)
    total_kpi = 0
    if rows:
        total_kpi = sb_upsert('kpi_scores', rows, 'month,agent')
        log(f"  ✓ Upserted {total_kpi}/{len(rows)} KPI scores")
    else:
        log("  No KPI scores found — skipping")
    log("")

    # Step 6: Write audit log entry
    log("▶ Step 6: Writing audit log entry…")
    audit_row = [{
        'actor': 'migration_script',
        'action': 'gist_to_supabase_migration',
        'month': None,
        'details': {
            'claims_migrated': total_claims,
            'flags_migrated' : total_flags,
            'kpi_migrated'   : total_kpi,
            'months'         : [m[0] for m in MONTHS_TO_MIGRATE],
            'source'         : 'gist' if GIST_TOKEN and data else 'local_files',
        },
    }]
    r = requests.post(
        f'{SUPABASE_URL}/rest/v1/audit_log',
        headers=sb_headers(),
        json=audit_row,
        timeout=10,
    )
    if r.ok:
        log("  ✓ Audit log entry written")
    else:
        log(f"  ! Audit log write failed: HTTP {r.status_code}")
    log("")

    log("═══════════════════════════════════════════════════════════")
    log(f"  MIGRATION COMPLETE")
    log(f"    Claims    : {total_claims}")
    log(f"    Flags     : {total_flags}")
    log(f"    KPI scores: {total_kpi}")
    log("═══════════════════════════════════════════════════════════")
    log("")
    log("Next: verify in Supabase Table Editor, then deploy patched HTML files.")


if __name__ == '__main__':
    main()
