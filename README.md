# 🗺️ India Job Migration Dashboard

An interactive dashboard mapping job seeker migration flows across Indian states — powered by **Adzuna Jobs API** and **Census/PLFS migration data**, auto-refreshed daily via **GitHub Actions**.

🔗 **Live site:** `https://YOUR-USERNAME.github.io/india-job-migration-dashboard/`

![Auto-update](https://github.com/YOUR-USERNAME/india-job-migration-dashboard/actions/workflows/update_dashboard.yml/badge.svg)

---

## 📊 Features

| Tab | What it shows |
|---|---|
| **Overview** | KPI cards, job openings by state, top migration routes |
| **Arc Flow Map** | Animated origin → destination arcs, filterable by volume |
| **Chord Diagram** | Inter-state migration flows between top 12 states |
| **Job Heatmap** | Job density by state, filterable by sector |
| **Data Pipeline** | Code reference for the data pipeline |

---

## 🗂️ Repository Structure

```
├── index.html              ← Dashboard (served by GitHub Pages)
├── pipeline.py             ← Fetches data from Adzuna + Census
├── inject_data.py          ← Injects fresh JSON into index.html
├── migration_flows.json    ← Auto-generated output (committed by Actions)
├── last_updated.txt        ← Timestamp of last data refresh
├── census_d02_migrants.csv ← (Optional) Census D-02 data you downloaded
└── .github/
    └── workflows/
        └── update_dashboard.yml  ← GitHub Actions schedule
```

---

## 🚀 Setup Guide

### 1. Fork or clone this repo

```bash
git clone https://github.com/YOUR-USERNAME/india-job-migration-dashboard.git
cd india-job-migration-dashboard
```

### 2. Get a free Adzuna API key

1. Go to [developer.adzuna.com](https://developer.adzuna.com)
2. Sign up for a free account
3. Copy your **App ID** and **App Key**

### 3. Add secrets to GitHub

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"** and add:

| Secret name | Value |
|---|---|
| `ADZUNA_APP_ID` | Your Adzuna App ID |
| `ADZUNA_APP_KEY` | Your Adzuna App Key |

> ⚠️ Never paste your API keys directly into any file — always use GitHub Secrets.

### 4. Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` / `root`
4. Click **Save**

### 5. Trigger the first run

Go to **Actions** tab → **"Update Job Migration Dashboard"** → **"Run workflow"**

This will fetch live data and commit the updated `index.html` to your repo. Your site will reflect the new data within a minute.

---

## ⏰ Auto-refresh Schedule

The pipeline runs automatically **every day at 2:00 AM IST** (configured in `update_dashboard.yml`).

To change the schedule, edit the `cron` value in `.github/workflows/update_dashboard.yml`:

```yaml
# Examples:
- cron: '30 20 * * *'    # Daily at 2:00 AM IST
- cron: '30 20 * * 1'    # Every Monday at 2:00 AM IST
- cron: '30 20 1 * *'    # First day of every month
```

---

## 📥 Optional: Add Census Migration Data

For richer origin-state data, download the Census 2011 D-02 tables:

1. Visit [censusindia.gov.in/nada](https://censusindia.gov.in/nada/index.php/catalog/42597)
2. Download the D-02 CSV
3. Rename it `census_d02_migrants.csv`
4. Commit it to your repo

The pipeline will automatically use it on the next run.

---

## 🛠️ Local Development

```bash
pip install requests pandas
python pipeline.py       # generates migration_flows.json
python inject_data.py    # injects data into index.html
open index.html          # view in browser
```

---

## 📡 Data Sources

| Source | What it provides | Access |
|---|---|---|
| [Adzuna API](https://developer.adzuna.com) | Live job openings by state/city | Free API key |
| [Census D-02](https://censusindia.gov.in/nada) | Origin → destination migration flows | Free download |
| [PLFS 2020-21](https://microdata.gov.in/NADA/index.php/catalog/PLFS) | Employment + migration microdata | Free download |
| [Kaggle Naukri](https://www.kaggle.com/datasets/iqbal303/job-postings-dataset-from-naukri-com) | Static job postings snapshot | Free download |

---

## 📄 License

MIT — free to use, modify, and share.
