# IPL Deliveries Dashboard

Interactive Streamlit dashboard over ball-by-ball IPL data — season/team filters, top batters, bowlers, team stats, match outcomes, venues, and phase (powerplay/death) specialists.

## Run locally

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

Opens at `http://localhost:8501`.

## Deploy on Streamlit Community Cloud (free, public URL)

1. Push this repo to GitHub (public or private — Streamlit Cloud supports both once you sign in with GitHub).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, pick this repo/branch, and set the main file path to `dashboard/app.py`.
4. Deploy. You'll get a public URL like `https://your-app-name.streamlit.app` — share that link anywhere (WhatsApp, etc.).

## Data

Expects `ipl_deliveries_real (1).csv` in the repo root (ball-by-ball delivery data). See `dashboard/metrics.py` for team/venue name normalization applied on load.
