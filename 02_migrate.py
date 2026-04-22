"""
Miracle MD Dashboard — targets.json → Supabase migration
One-time script. Run after 01_schema.sql is executed.

Usage:
  py -3.11 02_migrate.py

Requires:
  pip install supabase
"""
import json
import sys
from pathlib import Path
from datetime import datetime

try:
    from supabase import create_client
except ImportError:
    print("❌ supabase library not installed")
    print("Run: py -3.11 -m pip install supabase")
    sys.exit(1)

# ── Config ─────────────────────────────────────────────
SUPABASE_URL = "https://rqitgmydcbyiygqjssrb.supabase.co"
SUPABASE_KEY = "sb_publishable_8xb7ZaHyr3OF3WNEqufuDg_67spOIFw"
TARGETS_FILE = Path("targets.json")

# Sections that go in targets_static (static JSON blobs)
STATIC_KEYS = [
    "brand_config",
    "group_brand_config",
    "inhouse_codes",
    "kpi_weights",
    "newbie_scheme",   # global newbie config only; per-agent tiers live in targets_agents
]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def main():
    # Load targets.json
    if not TARGETS_FILE.exists():
        log(f"❌ {TARGETS_FILE} not found. Run from md-dashboard folder.")
        sys.exit(1)

    with open(TARGETS_FILE, encoding="utf-8") as f:
        targets = json.load(f)

    log(f"Loaded targets.json ({len(targets)} top-level sections)")

    # Safety check — no exposed tokens
    for danger_key in ["gist_token", "gist_id"]:
        if danger_key in targets:
            log(f"⚠️  Removing {danger_key} (should not be in DB)")
            del targets[danger_key]

    # Connect to Supabase
    log("Connecting to Supabase...")
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # ── 1. AGENTS ─────────────────────────────────────────
    log("Migrating agents...")
    agents = targets.get("agents", {})
    rows = []
    for agent, cfg in agents.items():
        rows.append({
            "agent": agent,
            "is_newbie": cfg.get("is_newbie", False),
            "active": cfg.get("active", True),
            "is_new_this_month": cfg.get("is_new_this_month", False),
            "sales_progression": cfg.get("sales_progression"),
            "brand_commission": cfg.get("brand_commission"),
            "kpi_targets": cfg.get("kpi_targets"),
            "kpi_auto_base": cfg.get("kpi_auto_base"),
            "newbie_tiers": cfg.get("newbie_tiers"),
            "newbie_account_tiers": cfg.get("newbie_account_tiers"),
            "updated_by": "migration_script",
        })
    if rows:
        sb.table("targets_agents").upsert(rows).execute()
    log(f"  Upserted {len(rows)} agents")

    # ── 2. MONTHLY TARGETS ────────────────────────────────
    log("Migrating monthly_targets...")
    monthly = targets.get("monthly_targets", {})
    rows = []
    for month, agents_month in monthly.items():
        for agent, cfg in agents_month.items():
            rows.append({
                "month": month,
                "agent": agent,
                "is_newbie": cfg.get("is_newbie", False),
                "active": cfg.get("active", True),
                "sales_progression": cfg.get("sales_progression"),
                "brand_commission": cfg.get("brand_commission"),
                "kpi_targets": cfg.get("kpi_targets"),
                "kpi_overrides": cfg.get("kpi_overrides"),
                "updated_by": "migration_script",
            })
    if rows:
        # Supabase upsert in batches of 100
        for i in range(0, len(rows), 100):
            sb.table("targets_monthly").upsert(rows[i:i+100]).execute()
    log(f"  Upserted {len(rows)} monthly target rows")

    # ── 3. AGENT PINS ─────────────────────────────────────
    log("Migrating agent_pins...")
    pins = targets.get("agent_pins", {})
    rows = [{"agent": a, "pin": str(p)} for a, p in pins.items()]
    if rows:
        sb.table("targets_pins").upsert(rows).execute()
    log(f"  Upserted {len(rows)} pins")

    # ── 4. BIRTHDAY OVERRIDES ─────────────────────────────
    log("Migrating birthday_overrides...")
    bday = targets.get("birthday_overrides", {})
    rows = []
    for code, info in bday.items():
        if isinstance(info, dict):
            rows.append({
                "debtor_code": code,
                "birth_date": info.get("birth_date") or info.get("date") or "",
                "birth_month": info.get("birth_month") or info.get("month"),
            })
        else:
            # Sometimes stored as just a string (birth_date)
            rows.append({"debtor_code": code, "birth_date": str(info)})
    if rows:
        sb.table("targets_birthday_overrides").upsert(rows).execute()
    log(f"  Upserted {len(rows)} birthday overrides")

    # ── 5. GROUP BRAND TARGETS ────────────────────────────
    log("Migrating group_brand_targets...")
    gbt = targets.get("group_brand_targets", {})
    rows = [{"brand": brand, "target_ctn": float(tgt or 0)} for brand, tgt in gbt.items()]
    if rows:
        sb.table("targets_group_brand").upsert(rows).execute()
    log(f"  Upserted {len(rows)} group brand targets")

    # ── 6. STATIC CONFIG ──────────────────────────────────
    log("Migrating static config (JSON blobs)...")
    rows = []
    for key in STATIC_KEYS:
        if key in targets:
            rows.append({"key": key, "value": targets[key]})
    if rows:
        sb.table("targets_static").upsert(rows).execute()
    log(f"  Upserted {len(rows)} static config entries")

    # ── 7. SNAPSHOTS (optional, auto-generated) ───────────
    log("Migrating snapshots...")
    snap_count = 0
    for month, snap in targets.get("monthly_snapshots", {}).items():
        sb.table("targets_snapshots").upsert({
            "kind": "monthly", "month": month, "value": snap
        }).execute()
        snap_count += 1
    for month, snap in targets.get("penetration_snapshots", {}).items():
        sb.table("targets_snapshots").upsert({
            "kind": "penetration", "month": month, "value": snap
        }).execute()
        snap_count += 1
    log(f"  Upserted {snap_count} snapshots")

    # ── Summary ───────────────────────────────────────────
    log("")
    log("✅ Migration complete")
    log("")
    log("Verify in Supabase SQL editor:")
    log("  SELECT COUNT(*) FROM targets_agents;")
    log("  SELECT COUNT(*) FROM targets_monthly;")
    log("  SELECT COUNT(*) FROM targets_pins;")
    log("  SELECT COUNT(*) FROM targets_birthday_overrides;")
    log("  SELECT COUNT(*) FROM targets_group_brand;")
    log("  SELECT key FROM targets_static;")


if __name__ == "__main__":
    main()
