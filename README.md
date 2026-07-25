# CRE AI Agent

Automated commercial real estate pipeline for New Jersey: scrape LoopNet
listings, underwrite individual deals, and generate static dashboards.

This repo is the **frontend / dashboard + scraping layer**. The heavy
underwriting engine lives in the sibling repo
[`cre-underwriting`](https://github.com/girnarholdings/cre-underwriting),
which `rebuild_all.py` imports directly via `sys.path`.

## Architecture (1 paragraph)

A Firefox-driven Selenium scraper (`scraper.py`) pulls LoopNet NJ listings
through a remote-debugging session that is the only reliable way past Akamai,
writing the full dataset to `incoming/nj-full/`. The dataset backs a
Linear-themed Streamlit dashboard (`nj_dashboard.py`) and a static HTML mirror
(`nj-dashboard.html`). For per-deal deep dives, `rebuild_all.py` imports the
`cre-underwriting` engine (v3 `EnhancedPipelineOrchestrator`), runs each deal
JSON through the convexity/moat/offer pipeline, calls
`generate_dashboard()` to emit a self-contained HTML file per deal under
`dashboards/<name>/index.html`, and those per-deal dirs deploy to Vercel.

## Quick Start

```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Launch Firefox with remote debugging (required for the scraper only)
firefox --remote-debugging-port=9222 &

# 3. Scrape NJ listings → incoming/nj-full/{nj_all_listings.csv,json}
python3 scraper.py

# 4. Launch the Streamlit dashboard (uses existing CSV if present)
streamlit run nj_dashboard.py --server.port 8502

# 5. Rebuild all per-deal dashboards (needs sibling cre-underwriting repo)
python3 rebuild_all.py
```

> The dashboard can run on the existing committed dataset without Firefox or
> the scraper — step 2/3 are only needed to refresh the listing inventory.

## Key Commands

| Command | Purpose |
|---------|---------|
| `python3 scraper.py` | Scrape all NJ LoopNet pages → CSV/JSON in `incoming/nj-full/` |
| `streamlit run nj_dashboard.py` | Interactive NJ listings dashboard (localhost:8502) |
| `python3 rebuild_all.py` | Re-run the underwriting engine on 6 tracked deals and regenerate HTML dashboards |
| `pytest -q` | Run the test suite |

## Key Files

| File | Purpose |
|------|---------|
| `scraper.py` | Multi-page LoopNet scraper via Firefox CDP remote debugging |
| `nj_dashboard.py` | Streamlit dashboard — search/filter/sort 475 NJ listings |
| `nj-dashboard.html` | Static HTML version of the dashboard (Linear-inspired dark theme) |
| `rebuild_all.py` | Orchestrates 6 deals through the cre-underwriting engine → per-deal HTML |
| `incoming/nj-full/nj_all_listings.csv` | Full NJ dataset (475 rows, 237 cities) |
| `data.csv` | Dataset loaded by the Streamlit dashboard |
| `dashboards/<name>/index.html` | One static dashboard per tracked deal (Millburn, Hoboken, Irvington, …) |
| `boonton-cre/`, `landing/` | Standalone landing/feature pages |
| `tests/test_rebuild_inputs_tracked.py` | Guard: every dashboard input JSON in `rebuild_all.py` must be tracked & present |

## Pipeline Notes

- **Akamai bypass**: Only Firefox remote-debugging works. `curl_cffi`,
  `nodriver`, and `Camoufox` are all blocked. VPN datacenter IPs are fully
  blocked — residential IPs or a real browser are required.
- **Login wall**: LoopNet limits data for non-authenticated sessions. Best
  results when the Firefox session is logged into LoopNet before scraping.
- **Vercel deploys**: each `dashboards/<name>/` dir is deployed to its own
  Vercel project; URLs are listed in `rebuild_all.py`.

## Related

- [`cre-underwriting`](https://github.com/girnarholdings/cre-underwriting) —
  the convexity/moat/offer underwriting engine imported by `rebuild_all.py`.
- `HANDOFF.md` — current project state, what works, and next steps.
- `AGENTS.md` — conventions for AI agents working in this repo.
