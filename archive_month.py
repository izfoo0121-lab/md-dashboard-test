"""
Miracle MD Dashboard — Monthly Archive Helper
Captures end-of-month results per agent into Supabase agent_monthly_archive.

Reads from monthly snapshot file (data_{month}.json) — stable per-month archive.

Usage:
  py -3.11 05_archive.py                          # Archive current month from dashboard_data.json
  py -3.11 05_archive.py "Apr 26"                 # Archive Apr 26 from data_apr26.json
  py -3.11 05_archive.py "Apr 26" --method manual --by "isaac"
"""
import json
import sys
from pathlib import Path
from datetime import datetime

try:
    from supabase import create_client
except ImportError:
    print("❌ supabase library not installed. Run: py -3.11 -m pip install supabase")
    sys.exit(1)

SUPABASE_URL = "https://rqitgmydcbyiygqjssrb.supabase.co"
SUPABASE_KEY = "sb_publishable_8xb7ZaHyr3OF3WNEqufuDg_67spOIFw"
BASE_DIR = Path(__file__).parent


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def month_to_slug(month_label):
    """'Apr 26' -> 'apr26'"""
    return month_label.replace(" ", "").lower()


def load_month_data(month_label):
    """Load dashboard data for a specific month from its snapshot file.
    Falls back to dashboard_data.json if specific file not found."""
    slug = month_to_slug(month_label)
    monthly_file = BASE_DIR / f"data_{slug}.json"
    dashboard_file = BASE_DIR / "dashboard_data.json"

    if monthly_file.exists():
        log(f"Reading from {monthly_file.name}")
        with open(monthly_file, encoding="utf-8") as f:
            return json.load(f), True  # True = from monthly snapshot

    if dashboard_file.exists():
        log(f"⚠ {monthly_file.name} not found, using dashboard_data.json")
        with open(dashboard_file, encoding="utf-8") as f:
            return json.load(f), False

    return None, False


def extract_agent_archive(agent_code, agent_data, month):
    """Extract archiveable fields from dashboard JSON agent record."""
    sp = agent_data.get("sales_progression", {}) or {}
    bc = agent_data.get("brand_commission", {}) or {}
    nb = agent_data.get("newbie_scheme", {}) or {}
    kpi = agent_data.get("kpi", {}) or {}

    # Commission breakdown
    comm_normal = float(sp.get("reward", 0) or 0)
    comm_brand  = sum(float((v or {}).get("comm_earned", 0) or 0) for v in bc.values())
    comm_newbie_ctn = float(nb.get("ctn_reward", 0) or 0)
    comm_newbie_acc = float(nb.get("acc_reward", 0) or 0)

    # Campaigns: sum approved campaign rewards
    comm_campaigns = 0.0
    for camp in (agent_data.get("campaigns", []) or []):
        comm_campaigns += float(camp.get("approved_reward", 0) or 0)

    comm_total = comm_normal + comm_brand + comm_newbie_ctn + comm_newbie_acc + comm_campaigns

    # Activity
    total_ctn_paid    = float(sp.get("ctn_total", 0) or nb.get("normal_ctn", 0) or 0)
    total_ctn_invoice = float(agent_data.get("total_ctn_invoice", total_ctn_paid) or total_ctn_paid)
    active_debtors    = int(agent_data.get("active_debtor_count", 0) or 0)

    # KPI scores
    kpi1_score = float(kpi.get("kpi1_score", kpi.get("score", 0)) or 0)
    kpi2_score = float(kpi.get("kpi2_score", 0) or 0)

    # Brand performance
    brand_perf = {}
    for brand, b in bc.items():
        if not b:
            continue
        brand_perf[brand] = {
            "pen":        (b.get("penetration", {}) or {}).get("count", 0),
            "pen_target": (b.get("penetration", {}) or {}).get("target", 0),
            "ctn":        (b.get("ctn", {}) or {}).get("sold", 0),
            "ctn_target": (b.get("ctn", {}) or {}).get("target", 0),
            "status":     b.get("status", "none_hit"),
            "comm":       float(b.get("comm_earned", 0) or 0),
        }

    return {
        "month": month,
        "agent": agent_code,
        "total_ctn_paid": total_ctn_paid,
        "total_ctn_invoice": total_ctn_invoice,
        "active_debtors": active_debtors,
        "new_accounts": int(nb.get("new_accounts", 0) or 0),
        "comm_normal": comm_normal,
        "comm_brand": comm_brand,
        "comm_newbie_ctn": comm_newbie_ctn,
        "comm_newbie_acc": comm_newbie_acc,
        "comm_campaigns": comm_campaigns,
        "comm_total": comm_total,
        "kpi1_score": kpi1_score,
        "kpi2_score": kpi2_score,
        "kpi_details": kpi,
        "brand_performance": brand_perf,
        "sales_tier": sp.get("tier_hit", "") or "",
        "sales_tier_ctn": float(sp.get("tier_ctn", 0) or 0),
    }


def archive_month(month, method="manual", captured_by="admin"):
    """Archive a specific month. month is required (e.g. 'Apr 26')."""
    if not month:
        log("❌ Month required. Usage: py -3.11 05_archive.py \"Apr 26\"")
        return False

    data, from_snapshot = load_month_data(month)
    if not data:
        log(f"❌ No data file found for {month}")
        return False

    # Confirm month in dashboard matches requested
    actual_month = data.get("meta", {}).get("current_month") or data.get("current_month")
    if actual_month and actual_month != month:
        log(f"⚠ Dashboard reports month '{actual_month}' but archiving as '{month}'")
        if not from_snapshot:
            # If reading from dashboard_data.json and months don't match, abort
            log(f"❌ Safety check: refusing to archive '{month}' from non-matching dashboard")
            return False

    log(f"Archiving {month} as '{method}' by '{captured_by}'...")

    rows = []
    agents = data.get("agents", {})
    for agent_code, agent_data in agents.items():
        row = extract_agent_archive(agent_code, agent_data, month)
        row["captured_at"]    = datetime.now().isoformat()
        row["captured_method"] = method
        row["captured_by"]    = captured_by
        rows.append(row)

    if not rows:
        log("❌ No agents to archive")
        return False

    try:
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Upsert in batches
        for i in range(0, len(rows), 50):
            sb.table("agent_monthly_archive").upsert(rows[i:i+50]).execute()
        log(f"✅ Archived {len(rows)} agents for {month}")

        # Summary
        total_comm = sum(r["comm_total"] for r in rows)
        top = sorted(rows, key=lambda r: r["comm_total"], reverse=True)[:3]
        log(f"   Total team commission: RM {total_comm:,.2f}")
        log(f"   Top 3 earners:")
        for r in top:
            log(f"     {r['agent']}: RM {r['comm_total']:,.2f}")
        return True
    except Exception as e:
        log(f"❌ Archive upsert failed: {e}")
        return False


def main():
    args = sys.argv[1:]
    month = None
    method = "manual"
    captured_by = "admin"

    i = 0
    while i < len(args):
        a = args[i]
        if a == "--method" and i + 1 < len(args):
            method = args[i+1]; i += 2
        elif a == "--by" and i + 1 < len(args):
            captured_by = args[i+1]; i += 2
        elif not a.startswith("--"):
            month = a; i += 1
        else:
            i += 1

    ok = archive_month(month=month, method=method, captured_by=captured_by)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
