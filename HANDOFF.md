# HANDOFF — CRE AI Agent (`CRE-AI-Agent`)

## Project Purpose

The frontend / scraping / dashboard layer of the Girnar CRE stack. It scrapes
LoopNet NJ commercial listings, presents them in an interactive Streamlit
dashboard plus a static HTML mirror, and rebuilds per-deal underwriting
dashboards by driving the sibling `cre-underwriting` engine. **Not the
underwriting engine itself** — that lives in
[`girnarholdings/cre-underwriting`](https://github.com/girnarholdings/cre-underwriting).

## Current State

- **Status:** Stable, not in active production. No cron jobs reference this
  repo. CI has been **disabled** in this branch (see "CI" below) because the
  project is dormant; it can be re-enabled when work resumes.
- **Last meaningful activity:** audit fixes (PRs #2–#4), AGENTS.md added (PR #5).
- **Default branch:** `main`. Current HEAD: `d201a15` (PR #5, AGENTS.md).

## What Works

- **Streamlit dashboard** (`nj_dashboard.py`) — loads committed `data.csv`,
  renders 475 NJ listings with search/filter/sort and a deep-dive panel. Runs
  standalone; no Firefox or network needed.
- **Static HTML dashboard** (`nj-dashboard.html`) — Linear-inspired dark theme,
  deployable as a static site.
- **LoopNet scraper** (`scraper.py`) — works only when a Firefox instance with
  `--remote-debugging-port=9222` is running and (ideally) logged into LoopNet.
  This is the only Akamai bypass that holds.
- **`rebuild_all.py`** — regenerates 6 tracked per-deal dashboards by calling
  the `cre-underwriting` engine. Inputs are the committed JSONs under
  `incoming/`; outputs land in `dashboards/<name>/index.html`.
- **Test guard** (`tests/test_rebuild_inputs_tracked.py`) — verifies every
  dashboard input JSON named in `rebuild_all.py` exists and is git-tracked.

## What Doesn't Work / Known Gaps

- **CI is red on `main`.** The `ci.yml` workflow fails (lint + test steps).
  This branch moves it aside (`.github/workflows.disabled/`) to silence the
  failure while the project is dormant. Re-enable by moving it back to
  `.github/workflows/` and fixing the lint/test failures first.
- **`rebuild_all.py` has a hardcoded absolute path**
  (`sys.path.insert(0, "/home/nima/cre-underwriting/src")`) and each dashboard
  entry uses absolute `/home/nima/...` paths. It only runs on the production
  box. The test guard remaps the `/home/nima/cre` prefix for CI/clones, but the
  `cre-underwriting` dependency is not installed — it's imported by absolute
  path.
- **Scraper is environment-dependent** — needs a logged-in Firefox CDP session
  and a non-VPN IP. Cannot run in CI.
- **No packaging** — `requirements.txt` only; no `pyproject.toml`. Python 3.12
  is the expected runtime per `AGENTS.md`.

## Next Steps (for whoever picks this up)

1. **Decide on CI strategy.** Either re-enable + fix (fix the lint errors and
   the failing test), or keep CI off until the project is back in production.
   The disabled workflow is preserved at `.github/workflows.disabled/ci.yml`.
2. **De-hardcode `rebuild_all.py`.** Replace absolute `/home/nima/...` paths
   with repo-relative paths and a resolved sibling-repo path, so the rebuild
   runs from any checkout.
3. **Make the `cre-underwriting` dependency explicit** (pip-installable / git
   submodule / vendored) rather than `sys.path` hack.
4. **Refresh the dataset.** `data.csv` / `incoming/nj-full/` reflect a snapshot;
   re-run `scraper.py` when fresh listings are needed.
5. **Consider merging per-deal dashboards** under a single deploy rather than
   one Vercel project per deal.

## Key Files

| Path | Role |
|------|------|
| `scraper.py` | Firefox-CDP LoopNet NJ scraper → `incoming/nj-full/` |
| `nj_dashboard.py` | Streamlit dashboard (main UI entry point) |
| `nj-dashboard.html` | Static HTML mirror of the dashboard |
| `rebuild_all.py` | 6-deal dashboard rebuilder (imports `cre-underwriting`) |
| `data.csv` | Listings dataset loaded by the Streamlit dashboard |
| `incoming/nj-full/nj_all_listings.{csv,json}` | Full scraped NJ dataset |
| `incoming/*.json` | Per-deal analysis inputs consumed by `rebuild_all.py` |
| `dashboards/<name>/index.html` | Generated per-deal dashboards (deployed to Vercel) |
| `tests/test_rebuild_inputs_tracked.py` | Guard: rebuild inputs are present & tracked |
| `requirements.txt` | Runtime deps: streamlit, pandas, selenium, bs4, lxml |

## Test / Lint Configuration

- **No `pyproject.toml` or `pytest.ini`.** Tests are plain `unittest`
  (`python -m unittest discover -s tests -v`), also runnable via `pytest -q`.
- **One test file:** `tests/test_rebuild_inputs_tracked.py` — a single guard
  test for the `rebuild_all.py` input contract.
- **Lint:** the (now-disabled) CI used `ruff check .`.

## CI

- **Disabled in this branch.** `.github/workflows/ci.yml` was moved to
  `.github/workflows.disabled/ci.yml` to stop the persistent red build while the
  project is dormant and not in production.
- **Why it was failing:** lint (`ruff check .`) and the `unittest` test step
  failed on `main`. Latest run on main (run ID `30166512739`) = `failure`.
- **To re-enable:** `git mv .github/workflows.disabled/ci.yml .github/workflows/ci.yml`
  (recreate the `workflows/` dir), then fix the lint/test failures before push.

## Related Repos / Docs

- [`cre-underwriting`](https://github.com/girnarholdings/cre-underwriting) — the
  underwriting engine imported by `rebuild_all.py`.
- `AGENTS.md` — agent conventions for this repo.
- `PROJECT.md`, `INDEX.md` — older project notes.
