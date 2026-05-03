"""
India Job Migration Dashboard — Data Pipeline
==============================================
Fetches job openings from Adzuna API + merges with Census/PLFS migration data
Then outputs migration_flows.json for the dashboard.

Setup:
  pip install requests pandas plotly dash folium

Usage:
  1. Set your Adzuna API credentials below (free at developer.adzuna.com)
  2. Download Census D-02 CSV from censusindia.gov.in/nada
  3. Run: python pipeline.py
  4. Run: python app.py  (launches dashboard at localhost:8050)
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime

# ─── CONFIG ──────────────────────────────────────────────────────────────────
ADZUNA_APP_ID  = os.getenv("ADZUNA_APP_ID",  "your_app_id_here")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "your_app_key_here")
CENSUS_CSV     = "census_d02_migrants.csv"   # Download from censusindia.gov.in
OUTPUT_FILE    = "migration_flows.json"

INDIA_STATES = [
    "Maharashtra", "Karnataka", "Tamil Nadu", "Delhi", "Telangana",
    "Gujarat", "West Bengal", "Uttar Pradesh", "Bihar", "Rajasthan",
    "Madhya Pradesh", "Andhra Pradesh", "Odisha", "Jharkhand",
    "Punjab", "Haryana", "Kerala", "Assam", "Uttarakhand",
]

# ─── STEP 1: FETCH JOB OPENINGS FROM ADZUNA ──────────────────────────────────
def fetch_jobs_for_state(state: str, max_pages: int = 5) -> list:
    """Fetch all job listings for a given Indian state via Adzuna API."""
    all_jobs = []
    for page in range(1, max_pages + 1):
        try:
            resp = requests.get(
                f"https://api.adzuna.com/v1/api/jobs/in/search/{page}",
                params={
                    "app_id":          ADZUNA_APP_ID,
                    "app_key":         ADZUNA_APP_KEY,
                    "where":           state,
                    "results_per_page": 50,
                    "content-type":    "application/json",
                },
                timeout=10
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if not results:
                break

            for job in results:
                all_jobs.append({
                    "title":    job.get("title", ""),
                    "company":  job.get("company", {}).get("display_name", ""),
                    "location": job.get("location", {}).get("display_name", ""),
                    "state":    state,
                    "category": job.get("category", {}).get("label", "Other"),
                    "salary_min": job.get("salary_min", 0),
                    "salary_max": job.get("salary_max", 0),
                    "created":  job.get("created", ""),
                    "url":      job.get("redirect_url", ""),
                })
        except requests.RequestException as e:
            print(f"  ⚠ Error fetching page {page} for {state}: {e}")
            break
    return all_jobs


def fetch_all_jobs() -> pd.DataFrame:
    """Loop all states and compile job listings."""
    print("📡 Fetching job data from Adzuna API...")
    all_jobs = []
    for state in INDIA_STATES:
        print(f"  → {state}...", end=" ", flush=True)
        jobs = fetch_jobs_for_state(state)
        all_jobs.extend(jobs)
        print(f"{len(jobs)} listings")

    df = pd.DataFrame(all_jobs)
    print(f"✅ Total job listings fetched: {len(df):,}\n")
    df.to_csv("adzuna_jobs_raw.csv", index=False)
    return df


# ─── STEP 2: LOAD CENSUS MIGRATION DATA ──────────────────────────────────────
def load_census_migration() -> pd.DataFrame:
    """
    Load Census 2011 D-02 migration data.
    
    Expected CSV columns (from censusindia.gov.in D-02 tables):
      state_of_last_residence, state_of_enumeration, 
      reason_for_migration, persons, males, females
    
    Download from:
      https://censusindia.gov.in/nada/index.php/catalog/42597
    """
    if not os.path.exists(CENSUS_CSV):
        print(f"⚠ Census file '{CENSUS_CSV}' not found.")
        print("  Using PLFS 2020-21 sample migration data instead...\n")
        return _generate_sample_migration()

    print(f"📂 Loading census migration data from {CENSUS_CSV}...")
    df = pd.read_csv(CENSUS_CSV)
    print(f"  Columns found: {list(df.columns)}")

    # Standardise column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Filter for work-related migration only
    work_reasons = ["work/employment", "business", "employment", "work"]
    if "reason_for_migration" in df.columns:
        df = df[df["reason_for_migration"].str.lower().isin(work_reasons)]
        print(f"  Work/employment migrants: {len(df):,} rows")

    print(f"✅ Migration data loaded: {len(df):,} records\n")
    return df


def _generate_sample_migration() -> pd.DataFrame:
    """Fallback: built-in sample data mirroring PLFS 2020-21 work migration patterns."""
    sample = [
        ("Uttar Pradesh","Delhi",1850000),("Uttar Pradesh","Maharashtra",620000),
        ("Uttar Pradesh","Karnataka",380000),("Uttar Pradesh","Gujarat",310000),
        ("Uttar Pradesh","Haryana",290000),("Bihar","Delhi",1420000),
        ("Bihar","Maharashtra",540000),("Bihar","West Bengal",290000),
        ("Bihar","Gujarat",280000),("Bihar","Uttar Pradesh",180000),
        ("Rajasthan","Delhi",610000),("Rajasthan","Gujarat",310000),
        ("Rajasthan","Maharashtra",240000),("Madhya Pradesh","Maharashtra",420000),
        ("Madhya Pradesh","Gujarat",280000),("Madhya Pradesh","Delhi",190000),
        ("Odisha","Maharashtra",310000),("Odisha","Gujarat",220000),
        ("Odisha","Karnataka",180000),("West Bengal","Maharashtra",280000),
        ("West Bengal","Delhi",190000),("West Bengal","Karnataka",160000),
        ("Jharkhand","Delhi",210000),("Jharkhand","Maharashtra",180000),
        ("Andhra Pradesh","Telangana",380000),("Andhra Pradesh","Karnataka",290000),
        ("Andhra Pradesh","Tamil Nadu",180000),("Tamil Nadu","Karnataka",240000),
        ("Tamil Nadu","Maharashtra",210000),("Kerala","Karnataka",160000),
        ("Kerala","Tamil Nadu",140000),("Assam","Delhi",120000),
        ("Punjab","Delhi",180000),("Haryana","Delhi",340000),
        ("Uttarakhand","Delhi",190000),("Gujarat","Maharashtra",210000),
        ("Karnataka","Maharashtra",140000),("Telangana","Maharashtra",120000),
        ("Assam","Maharashtra",90000),("Himachal Pradesh","Delhi",80000),
    ]
    df = pd.DataFrame(sample, columns=[
        "state_of_last_residence", "state_of_enumeration", "persons"
    ])
    df["reason_for_migration"] = "work/employment"
    return df


# ─── STEP 3: MERGE AND BUILD FLOW DATASET ────────────────────────────────────
def build_flow_dataset(df_jobs: pd.DataFrame, df_migration: pd.DataFrame) -> pd.DataFrame:
    """Merge job openings with migration flows to produce the final dataset."""
    print("🔄 Merging job openings with migration flows...")

    # Count job openings per state
    job_counts = (
        df_jobs.groupby("state")["title"]
        .count()
        .reset_index()
        .rename(columns={"title": "job_openings"})
    )

    # Normalise column names in migration df
    origin_col = "state_of_last_residence"
    dest_col   = "state_of_enumeration"
    persons_col= "persons"

    # Aggregate by origin → destination
    flows = (
        df_migration.groupby([origin_col, dest_col])[persons_col]
        .sum()
        .reset_index()
        .rename(columns={
            origin_col:  "origin",
            dest_col:    "destination",
            persons_col: "migrants"
        })
    )

    # Merge with job openings at destination
    flows = flows.merge(
        job_counts.rename(columns={"state":"destination","job_openings":"dest_job_openings"}),
        on="destination", how="left"
    ).fillna({"dest_job_openings": 0})

    # Merge with job openings at origin (out-push factor)
    flows = flows.merge(
        job_counts.rename(columns={"state":"origin","job_openings":"origin_job_openings"}),
        on="origin", how="left"
    ).fillna({"origin_job_openings": 0})

    # Migration pressure index (migrants per job opening)
    flows["migration_pressure"] = (
        flows["migrants"] / (flows["dest_job_openings"] + 1)
    ).round(2)

    # Flow category
    def categorise(m):
        if m >= 1_000_000: return "high"
        if m >= 300_000:   return "medium"
        return "low"
    flows["volume_category"] = flows["migrants"].apply(categorise)

    flows = flows.sort_values("migrants", ascending=False).reset_index(drop=True)
    print(f"✅ Flow dataset built: {len(flows)} origin→destination pairs\n")
    return flows


# ─── STEP 4: EXPORT ──────────────────────────────────────────────────────────
def export_output(df_flows: pd.DataFrame, df_jobs: pd.DataFrame):
    """Export final JSON and CSVs for the dashboard."""

    # Job openings per state
    job_by_state = (
        df_jobs.groupby(["state", "category"])
        .size().reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    output = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_job_openings": int(len(df_jobs)),
            "total_migration_routes": int(len(df_flows)),
            "total_migrants": int(df_flows["migrants"].sum()),
            "states_covered": int(df_flows["destination"].nunique()),
        },
        "migration_flows": df_flows.to_dict(orient="records"),
        "job_openings_by_state": job_by_state.to_dict(orient="records"),
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, default=str)

    df_flows.to_csv("migration_flows.csv", index=False)
    print(f"💾 Output saved to: {OUTPUT_FILE}")
    print(f"💾 CSV saved to:    migration_flows.csv")
    print(f"\n{'─'*50}")
    print("📊 Summary:")
    print(f"   Total job openings tracked : {output['summary']['total_job_openings']:>10,}")
    print(f"   Migration routes mapped    : {output['summary']['total_migration_routes']:>10,}")
    print(f"   Estimated total migrants   : {output['summary']['total_migrants']:>10,}")
    print(f"   Destination states covered : {output['summary']['states_covered']:>10}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  India Job Migration Dashboard — Pipeline")
    print("=" * 50 + "\n")

    # Step 1: Jobs
    if ADZUNA_APP_ID != "your_app_id_here":
        df_jobs = fetch_all_jobs()
    else:
        print("⚠ No Adzuna credentials set. Using sample job data.")
        print("  Get free API keys at: https://developer.adzuna.com\n")
        # Sample fallback job data
        sample_jobs = []
        job_counts = {
            "Maharashtra":185000,"Karnataka":162000,"Delhi":134000,"Tamil Nadu":98000,
            "Telangana":91000,"Gujarat":76000,"West Bengal":54000,"Haryana":48000,
        }
        categories = ["IT","Finance","Manufacturing","Healthcare","Retail","Education"]
        import random
        for state, count in job_counts.items():
            for i in range(min(count//1000, 50)):
                sample_jobs.append({
                    "title":f"Job {i+1}","company":f"Company {i}",
                    "location":state,"state":state,
                    "category":random.choice(categories),
                    "salary_min":300000,"salary_max":800000,
                    "created":datetime.now().isoformat(),"url":""
                })
        df_jobs = pd.DataFrame(sample_jobs)

    # Step 2: Migration origins
    df_migration = load_census_migration()

    # Step 3: Merge
    df_flows = build_flow_dataset(df_jobs, df_migration)

    # Step 4: Export
    export_output(df_flows, df_jobs)

    print("\n✅ Pipeline complete! Open india_migration_dashboard.html to view.")
