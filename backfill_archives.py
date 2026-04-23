"""
Miracle MD Dashboard — Monthly Archive Backfill
Scans for all data_*.json files and archives each month.

Usage:
  py -3.11 backfill_archives.py              # Backfill all months found
  py -3.11 backfill_archives.py --force      # Re-archive even if already archived
"""
import sys
import re
from pathlib import Path
from datetime import datetime

try:
    from supabase import create_client
except ImportError:
    print("❌ supabase library not installed. Run: py -3.11 -m pip install supabase")
    sys.exit(1)

# Import archive logic from archive_month.py (must be in same folder)
sys.path.insert(0, str(Path(__file__).parent))
archive_mod = None
try:
    import archive_month as archive_mod
except ImportError:
    try:
        # Fallback to old name
        from importlib import import_module
        archive_mod = import_module("05_archive")
    except ImportError:
        archive_mod = None

SUPABASE_URL = "https://rqitgmydcbyiygqjssrb.supabase.co"
SUPABASE_KEY = "sb_publishable_8xb7ZaHyr3OF3WNEqufuDg_67spOIFw"
BASE_DIR = Path(__file__).parent

MONTH_NAMES = {"jan":"Jan","feb":"Feb","mar":"Mar","apr":"Apr","may":"May","jun":"Jun",
               "jul":"Jul","aug":"Aug","sep":"Sep","oct":"Oct","nov":"Nov","dec":"Dec"}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def slug_to_label(slug):
    """'apr26' -> 'Apr 26'"""
    m = re.match(r"([a-z]{3})(\d{2})", slug.lower())
    if not m:
        return None
    name, yr = m.groups()
    return f"{MONTH_NAMES.get(name, name.title())} {yr}"


def main():
    force = "--force" in sys.argv

    if not archive_mod or not hasattr(archive_mod, "archive_month"):
        log("❌ archive_month.py not found in same folder as backfill script")
        log("   Place archive_month.py in C:\\Users\\tgy_3\\Desktop\\md-dashboard\\")
        sys.exit(1)

    # Find all data_*.json files
    files = sorted(BASE_DIR.glob("data_*.json"))
    if not files:
        log("No data_*.json files found. Run update_dashboard.bat for some months first.")
        return

    log(f"Found {len(files)} monthly snapshot files:")
    for f in files:
        log(f"  {f.name}")
    log("")

    # Check which are already archived
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    try:
        existing = sb.table("agent_monthly_archive").select("month").execute()
        archived_months = set(r["month"] for r in (existing.data or []))
        log(f"Already archived: {len(archived_months)} months ({', '.join(sorted(archived_months)) or 'none'})")
    except Exception as e:
        log(f"⚠ Could not check existing archives: {e}")
        archived_months = set()
    log("")

    # Archive each
    success = 0
    skipped = 0
    failed = 0
    for f in files:
        slug = f.stem.replace("data_", "")
        month = slug_to_label(slug)
        if not month:
            log(f"⚠ Skipping {f.name}: cannot parse month")
            failed += 1
            continue

        if month in archived_months and not force:
            log(f"⏭  {month}: already archived (use --force to overwrite)")
            skipped += 1
            continue

        ok = archive_mod.archive_month(month=month, method="backfill", captured_by="backfill_script")
        if ok:
            success += 1
        else:
            failed += 1
        log("")

    log("========== BACKFILL SUMMARY ==========")
    log(f"  Archived successfully: {success}")
    log(f"  Skipped (already done): {skipped}")
    log(f"  Failed: {failed}")
    log("======================================")


if __name__ == "__main__":
    main()
