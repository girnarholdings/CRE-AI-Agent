# CRE AI Agent

Automated commercial real estate pipeline: LoopNet scraping → underwriting → Streamlit dashboard.

## Architecture

```
LoopNet (Akamai-protected)
    │
    ▼
Firefox remote-debugging (Selenium)  ←  only bypass that works
    │
    ▼
NJ property scraper  →  CSV / JSON
    │
    ▼
Streamlit dashboard  →  localhost:8502
    │
    ▼
Underwriting playbook (per-deal deep dive)
```

## Quick Start

```bash
# 1. Launch Firefox with remote debugging
firefox --remote-debugging-port=9222 &

# 2. Scrape NJ listings
python3 ~/.hermes/scripts/loopnet_nj_full_scrape.py

# 3. Launch dashboard
streamlit run nj_dashboard.py --server.port 8502
```

## Files

| File | Purpose |
|------|---------|
| `nj_dashboard.py` | Streamlit dashboard — 475 NJ listings with search, filter, sort |
| `nj-dashboard.html` | Static HTML version (Linear-inspired dark theme) |
| `~/.hermes/scripts/loopnet_nj_full_scrape.py` | Multi-page LoopNet scraper via Firefox CDP |
| `incoming/nj-full/nj_all_listings.csv` | Full NJ dataset (475 rows) |
| `incoming/nj-full/nj_all_listings.json` | JSON export |

## Pipeline Notes

- **Akamai bypass**: Only Firefox remote-debugging works. curl_cffi, nodriver, Camoufox all blocked.
- **VPN datacenters**: Fully blocked by Akamai. Residential IPs or real browser required.
- **Login**: LoopNet login wall limits data for non-authenticated sessions. Best results when logged in.

## Dashboard Features

- 475 NJ commercial properties for sale
- 237 unique cities, 10 property types
- Price range: $39,900 – $34,000,000 (median $1,495,000)
- Linear-inspired dark theme (#08090a, Inter font, indigo accent)
- Search, filter by type, sort by price/SF/city
- Deep dive panel — select listing # for full underwriting
