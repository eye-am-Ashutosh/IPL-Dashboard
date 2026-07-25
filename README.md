# IPL Deliveries Dashboard

An interactive Streamlit dashboard built over ~296,000 rows of ball-by-ball IPL data (2008–2026) — season/team filters drive batter and bowler leaderboards, team win-loss records, venue analytics, and phase-specific breakdowns (powerplay vs. death-overs specialists).

**Live app:** https://ipl-dashboard-detailed.streamlit.app/
*(free-tier hosting — first load may take a few seconds to wake up)*

## What it does

- **Overview** — scoring trends by season, run distribution, dismissal types, chase-vs-defend split, extras breakdown
- **Batting / Bowling** — filterable leaderboards (runs, strike rate, economy, average) plus powerplay and death-overs specialist rankings
- **Teams** — team totals, and head-to-head win/loss records against every opponent for a selected team and season range
- **Match Outcomes** — derived match winners, margins, and how each match was decided (runs, wickets, or Super Over)
- **Venues** — average and highest innings scores per ground
- **Top Innings** — highest team totals across seasons

## Technical highlights

- **Data cleaning at scale**: the raw data had inconsistent team names (e.g. "Kings XI Punjab" vs "Punjab Kings") and heavily fragmented venue names (60 raw strings collapsed to 36 real stadiums — e.g. "Wankhede Stadium" and "Wankhede Stadium, Mumbai" were the same ground). Wrote normalization logic so stats aggregate correctly instead of silently splitting across duplicate labels.
- **Derived match outcomes from raw deliveries**: there's no "winner" column in the source data — match results (including Super Overs and no-results) are computed by comparing per-innings totals.
- **Filter correctness**: a team filter has to distinguish "matches this team played in" (needed for match-level context) from "this team's own batting/bowling stats" (needed for leaderboards) — conflating the two silently pulls in opponents' stats, an easy bug to miss.
- **Deployment-size optimization**: gzip-compressed the dataset (39MB → 2.1MB) with zero data loss for a faster, GitHub-web-upload-friendly deploy.

## Tech stack

Python · Streamlit · Pandas · Plotly

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`.

## Data

Expects `ipl_deliveries_real (1).csv.gz` in the repo root (ball-by-ball delivery data, gzip-compressed). See `metrics.py` for the team/venue/season name normalization applied on load.
