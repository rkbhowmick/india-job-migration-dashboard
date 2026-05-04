"""
inject_data.py
==============
Reads the freshly generated migration_flows.json from pipeline.py
and injects it into index.html so the dashboard always shows live data.

Also writes last_updated.txt so the dashboard can display a "last refreshed" badge.

Run automatically by GitHub Actions after pipeline.py completes.
"""

import json
import re
from datetime import datetime, timezone, timedelta

# IST = UTC + 5:30
IST = timezone(timedelta(hours=5, minutes=30))

# ─── Load fresh data ──────────────────────────────────────────────────────────
with open("migration_flows.json") as f:
    data = json.load(f)

flows     = data.get("migration_flows", [])
summary   = data.get("summary", {})
job_state = data.get("job_openings_by_state", [])

# Build job hotspot dict  {state: total_openings}
job_hotspots = {}
for row in job_state:
    state = row.get("state", "")
    count = row.get("count", 0)
    job_hotspots[state] = job_hotspots.get(state, 0) + count

# ─── Build JS data block to inject ───────────────────────────────────────────
timestamp = datetime.now(IST).strftime("%d %b %Y, %H:%M IST")

js_block = f"""
// ── AUTO-INJECTED BY inject_data.py — DO NOT EDIT MANUALLY ──
// Last refreshed: {timestamp}
const LIVE_SUMMARY = {json.dumps(summary, indent=2)};
const LIVE_MIGRATION_FLOWS = {json.dumps(flows, indent=2)};
const LIVE_JOB_HOTSPOTS = {json.dumps(job_hotspots, indent=2)};
const LAST_UPDATED = "{timestamp}";
// ── END INJECTED DATA ──
"""

# ─── Inject into index.html ───────────────────────────────────────────────────
with open("index.html") as f:
    html = f.read()

# Replace the data block between markers (or append before </script> close)
marker_start = "// ── AUTO-INJECTED BY inject_data.py — DO NOT EDIT MANUALLY ──"
marker_end   = "// ── END INJECTED DATA ──"

if marker_start in html:
    # Replace existing block
    pattern = re.escape(marker_start) + r".*?" + re.escape(marker_end)
    html = re.sub(pattern, js_block.strip(), html, flags=re.DOTALL)
    print("✅ Replaced existing data block in index.html")
else:
    # First time — insert after the opening <script> tag that contains the data
    # Find the line with "const STATE_COORDS_PROJ" and insert before it
    insert_before = "const STATE_COORDS_PROJ"
    if insert_before in html:
        html = html.replace(insert_before, js_block + "\n" + insert_before, 1)
        print("✅ Injected data block into index.html (first time)")
    else:
        # Fallback: append just before </script>
        html = html.replace("</script>", js_block + "\n</script>", 1)
        print("✅ Injected data block into index.html (fallback)")

# Update the live badge text
html = html.replace(
    'Adzuna + PLFS 2021',
    f'Live · Updated {datetime.now(IST).strftime("%d %b %Y")}'
)

# Update header stats with real numbers
total_jobs = summary.get("total_job_openings", 0)
total_routes = summary.get("total_migration_routes", 0)

with open("index.html", "w") as f:
    f.write(html)

# ─── Write timestamp file ─────────────────────────────────────────────────────
with open("last_updated.txt", "w") as f:
    f.write(timestamp)

print(f"📅 Last updated: {timestamp}")
print(f"💼 Total jobs: {total_jobs:,}")
print(f"🗺  Migration routes: {total_routes}")
print("✅ inject_data.py complete")
