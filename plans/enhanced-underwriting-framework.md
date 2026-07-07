# Enhanced CRE Underwriting Framework — Implementation Plan

> **For Hermes:** Execute sequentially. Framework applies to Augusta Rd property as first test case, then saves as reusable skill.

**Goal:** Replace the single-pipeline underwriting with an 8-pillar framework that drives every deal analysis: valuation triangulation → comps → HPA → financial levers → demographics → frontier graph → scenarios → comprehensive output.

**Architecture:** Each pillar is an independent Python module. The orchestrator composes them. Output flows into the existing dashboard generator. New data sources: FRED API, Census API, LoopNet scraping, county assessor.

**Tech Stack:** Python 3.11, cre_underwriting package, FRED API key, Selenium/Firefox BiDi, matplotlib (frontier graph)

---

## Pillar 1: Valuation Triangulation

### Task 1.1: Build Land Value Estimator
- **File:** `src/cre_underwriting/valuation.py`
- **Logic:** Extract land from assessor (improvements vs land split), cross-reference with recent land sales comps in same corridor, use price/acre from LoopNet land listings
- **Output:** `{land_value_low, mid, high, methodology}`

### Task 1.2: Build Building/PPE Estimator
- **Logic:** Replacement cost per SF by property type × building class × region. Depreciation schedule (age, renovation year). Equipment: HVAC estimate by SF, specialized equipment detection from listing text.
- **Output:** `{building_value_low, mid, high, equipment_value, depreciation_pct}`

### Task 1.3: License Detection & Valuation
- **Logic:** Scan listing for: liquor license, beer/wine license, gas station license, distribution license, cannabis license (state-dependent), PILOT agreements, tax abatements. Look up state-specific transferability and market value.
- **Output:** `{licenses: [{type, value, transferable, source}], total_license_value}`

### Task 1.4: Triangulation Summary
- **Logic:** Merge land + building + equipment + licenses → three-point estimate (low/mid/high). Compare to ask price. Flag if hard assets alone justify any % of ask.
- **Output:** `{hard_asset_value_low, mid, high, vs_ask_pct, gap_explanation}`

---

## Pillar 2: Comparable Properties

### Task 2.1: Enhanced Comp Scraper
- **Logic:** Search LoopNet for same property type, within 5-mile radius, similar SF (±50%), sold AND active. Extract: price, SF, $/SF, cap rate, NOI, year built, lot size, tenant mix text. Sort by proximity × similarity score.
- **Output:** `[{address, price, sf, psf, cap_rate, noi, year_built, distance_mi, similarity_score, status}]`

### Task 2.2: Revenue Estimation from Comps
- **Logic:** If comp has NOI → back out revenue. If comp has rent roll → aggregate. Build revenue/SF range for submarket.
- **Output:** `{revenue_psf_range, expense_ratio_range, market_noi_margin}`

### Task 2.3: Comp-Based Valuation
- **Logic:** Apply comp $/SF range to subject SF → value range. Apply comp cap rate range to subject NOI → value range. Weight by similarity score.
- **Output:** `{comp_based_value_low, mid, high, comp_count, confidence}`

---

## Pillar 3: Home Price Appreciation

### Task 3.1: FRED MSA-Level HPI Pull
- **Logic:** Pull FRED series for Greenville-Anderson MSA (or nearest). All-transactions HPI, 1-year, 3-year, 5-year annualized. Compare to national and state.
- **Output:** `{msa_name, hpi_1yr, hpi_3yr, hpi_5yr, vs_national, vs_state}`

### Task 3.2: Zip/County Level from Census/Zillow
- **Logic:** Pull ACS median home value 1yr/5yr change for zip 29605 and Greenville County. Cross-reference with ZHVI if accessible.
- **Output:** `{zip_median_home_value, zip_1yr_change_pct, county_median, county_1yr_change}`

### Task 3.3: HPA Context for CRE
- **Logic:** Strong residential HPA → retail demand follows (new rooftops → new retail need). Lag of 12-24 months. Score the tailwind.
- **Output:** `{hpa_tailwind_score, narrative, data_quality}`

---

## Pillar 4: Financial & Business Levers

### Task 4.1: Base Case Financial Model
- **Logic:** Build 5-year pro forma with: gross rent, vacancy (market + property-specific), operating expenses (by lease type), property taxes (post-sale), debt service (if financed), net cash flow, exit value (cap rate method).
- **Output:** `{yearly_cashflows, irr_unlevered, irr_levered, equity_multiple, cash_on_cash}`

### Task 4.2: Business Lever Generator
- **Logic:** Property-type-specific lever catalog. For retail: add vending machines ($2-5K/yr), convert storage to rentable ($X/SF), add outdoor seating, add ATM, subdivide large bay, add cell tower lease, convert to smoke shop, add apartment unit (if zoning allows), add drive-thru. Score each by: revenue potential, capex required, zoning risk, timeline.
- **Output:** `[{lever, revenue_impact, capex, zoning_risk, timeline_months, score}]`

### Task 4.3: Lever-Enhanced Scenarios
- **Logic:** For each scenario, apply applicable levers. Phase 1 = low-capex levers. Phase 2 = medium-capex levers. Phase 3 = high-capex/structural.
- **Output:** Updated scenario values with explicit lever contributions.

---

## Pillar 5: Demographics & Migration

### Task 5.1: Census Tract Demographics
- **Logic:** Pull ACS 5-year for tract containing 3904-3914 Augusta Rd. Population, median income, poverty rate, education, employment. Compare to county and state.
- **Output:** `{tract_pop, pop_growth_5yr, median_hh_income, poverty_pct, bachelor_pct, unemployment_pct}`

### Task 5.2: Migration Analysis
- **Logic:** IRS SOI migration data (county-to-county flows). Net domestic migration for Greenville County. Age cohort breakdown if available.
- **Output:** `{net_domestic_migration, inflow_counties_top3, outflow_counties_top3, migration_score}`

### Task 5.3: Retail Demand Proxy
- **Logic:** Population growth × income growth → retail spending growth proxy. Compare per-capita retail SF in submarket to national average.
- **Output:** `{retail_demand_growth_pct, retail_sf_per_capita, vs_national, score}`

---

## Pillar 6: Effective Frontier Graph

### Task 6.1: Build Frontier Data Points
- **Logic:** For a range of purchase prices ($400K to $825K in $25K increments), compute: worst-case % of capital, best-case MOIC. Plot scatter with zone shading.
- **Output:** `[[price, worst_pct, best_moic, zone], ...]`

### Task 6.2: Generate SVG/PNG Graph
- **Logic:** matplotlib: scatter plot with zone coloring (green=aggressive, yellow=conditional, red=walk). Vertical line at ask price. Horizontal line at MOIC=1.0. Annotate the target offer point.
- **Output:** `frontier_graph.png` (embedded in dashboard)

---

## Pillar 7: Rigorous Scenario Analysis

### Task 7.1: Property-Type-Specific Scenario Catalog
- **Logic:** For RETAIL specifically: e-commerce disruption (Amazon effect), big-box anchor departure, pandemic shutdown, interest rate shock (cap rate expansion), corridor obsolescence (highway bypass), gentrification uplift, greenway/trail adjacency, major employer relocation. For OFFICE: WFH permanence, sublease shadow space, flight to quality. For INDUSTRIAL: nearshoring, last-mile demand. For MULTIFAMILY: rent control risk, supply wave.
- **Output:** Property-type-specific scenario templates.

### Task 7.2: Apply to Deal
- **Logic:** Select 5-7 scenarios most relevant to this specific property. Weight by probability. Compute exit value under each. Flag the ones that would wipe out equity.
- **Output:** Updated scenario list with property-type-specific risks.

---

## Pillar 8: Comprehensive Output

### Task 8.1: Merge All Pillars into Unified Analysis JSON
- **Logic:** Orchestrator calls each pillar, collects results, resolves conflicts, produces final analysis dict.
- **Output:** `comprehensive_analysis.json`

### Task 8.2: Enhanced Dashboard
- **Logic:** Update dashboard to include new tabs: Valuation Triangulation, Business Levers, Frontier Graph, Migration. Keep existing: Scenarios, Moats, Offers, Risks, Demographics, Environmental, Comps.
- **Output:** Updated `dashboard.html`

### Task 8.3: Save as Reusable Skill
- **Logic:** Package as `cre-underwriting-v3` skill. Reference: `skill_manage` action='create'. Include all new modules, the orchestrator, and the dashboard builder.
- **Output:** `~/.hermes/skills/finance/cre-underwriting-v3/SKILL.md`

---

## Execution Order

1. Pillar 3 (HPI) — quick FRED pull, provides market context
2. Pillar 5 (Demographics) — census API, fast
3. Pillar 2 (Comps) — LoopNet scraping, slower
4. Pillar 1 (Valuation) — depends on comps for land triangulation
5. Pillar 4 (Financial Levers) — depends on valuation for base case
6. Pillar 7 (Scenarios) — depends on all above for risk catalog
7. Pillar 6 (Frontier Graph) — depends on scenarios
8. Pillar 8 (Output) — synthesis
