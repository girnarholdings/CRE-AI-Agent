#!/usr/bin/env python3
"""
Rebuild all 6 CRE dashboards by running the fixed EnhancedPipelineOrchestrator
on deal data and deploying to Vercel.
"""
import json
import sys
import os
from pathlib import Path

# Add the cre-underwriting src to path
sys.path.insert(0, "/home/nima/cre-underwriting/src")

from cre_underwriting.orchestrator_v3 import EnhancedPipelineOrchestrator
from cre_underwriting.dashboard import generate_dashboard

# ── Dashboard definitions ──
DASHBOARDS = [
    {
        "name": "Millburn",
        "input": "/home/nima/cre/incoming/39473852_analysis.json",
        "output_dir": "/home/nima/cre/dashboards/millburn",
        "output_file": "index.html",
        "title": "519 Millburn Ave — Short Hills, NJ",
        "vercel_url": "https://millburn.vercel.app",
    },
    {
        "name": "Irvington",
        "input": "/home/nima/cre/incoming/listing_40306150_analysis.json",
        "output_dir": "/home/nima/cre/dashboards/irvington",
        "output_file": "index.html",
        "title": "216-218 Orange Ave — Irvington, NJ",
        "vercel_url": "https://irvington-nj.vercel.app",
    },
    {
        "name": "Hoboken",
        "input": "/home/nima/cre/incoming/40345122_pipeline_v4.json",
        "output_dir": "/home/nima/cre/dashboards/hoboken",
        "output_file": "index.html",
        "title": "87 Jefferson St — Hoboken, NJ",
        "vercel_url": "https://hoboken.vercel.app",
    },
    {
        "name": "Crown Point",
        "input": "/home/nima/cre/incoming/40480939_analysis.json",
        "output_dir": "/home/nima/cre/dashboards/crown-point",
        "output_file": "index.html",
        "title": "6 Crown Point Rd — West Deptford, NJ",
        "vercel_url": "https://crown-point.vercel.app",
    },
    {
        "name": "Augusta-Greenville",
        "input": "/home/nima/cre/incoming/40159875_analysis.json",
        "output_dir": "/home/nima/cre/dashboards/augusta-greenville",
        "output_file": "index.html",
        "title": "3904-3914 Augusta Rd — Greenville, SC",
        "vercel_url": "https://augusta-greenville.vercel.app",
    },
    {
        "name": "Urban-NJ / Passaic",
        "input": "/home/nima/cre/incoming/39810931_pipeline_v4.json",
        "output_dir": "/home/nima/cre/dashboards/urban-nj",
        "output_file": "index.html",
        "title": "4 Market St — Passaic, NJ",
        "vercel_url": "https://urban-nj.vercel.app",
    },
]


def is_pipeline_format(data):
    """Check if JSON is old pipeline output (has valuation_triangulation at top level)."""
    return "valuation_triangulation" in data and "convexity" in data


def extract_deal_from_pipeline(data):
    """
    Extract deal_data dict from a pipeline_v4 output so the orchestrator
    can re-run with fixed logic.
    """
    vt = data.get("valuation_triangulation", {})
    building = vt.get("building", {})
    land = vt.get("land", {})
    
    # Build property dict
    prop = {
        "address": data.get("address", ""),
        "listing_id": data.get("listing_id", ""),
        "price": data.get("ask_price", 0),
        "property_type": data.get("property_type", "Retail"),
        "sf": building.get("building_sf", 0),
        "building_size_sf": building.get("building_sf", 0),
        "lot_acres": land.get("lot_acres", 0),
        "year_built": building.get("year_built", 1970),
        "year_renovated": building.get("year_renovated"),
        "building_class": building.get("building_class", "C"),
        "state": data.get("state", "NJ"),
        "city": data.get("city", ""),
    }
    
    # Extract NOI from pro_forma or scenarios
    pro_forma = data.get("pro_forma", {})
    scenarios = data.get("scenarios", data.get("property_specific_scenarios", {}))
    
    noi = 0
    if pro_forma:
        # Try to get year-1 NOI
        yearly = pro_forma.get("yearly_projections", [])
        if yearly:
            noi = yearly[0].get("noi", 0) or 0
    if noi <= 0:
        # Try baseline scenario
        for k, v in scenarios.items():
            if "base" in k.lower() or "status quo" in k.lower():
                noi = v.get("noi", 0) or 0
                break
    if noi <= 0:
        # Fallback
        ask = data.get("ask_price", 0) or 0
        noi = ask * 0.075  # ~7.5% cap rate
    
    income = {
        "noi": noi,
        "gross_rent": noi * 1.6,  # rough estimate
    }
    
    # Hard asset floor from valuation
    hard_asset_floor = {
        "low": vt.get("hard_asset_value_low", 0),
        "mid": vt.get("hard_asset_value_mid", 0),
        "high": vt.get("hard_asset_value_high", 0),
    }
    
    # Build deal_data
    deal_data = {
        "property": prop,
        "income": income,
        "hard_asset_floor": hard_asset_floor,
        "purchase_price": data.get("ask_price", 0),
        "exit_cap_rate": data.get("pro_forma", {}).get("exit_cap_rate", 0.08) or 0.08,
        "exit_year": 5,
        "capital_invested": data.get("ask_price", 0),
        "tax": {
            "post_sale": {
                "annual_tax_estimated": pro_forma.get("annual_taxes_estimated", 0) or 0,
            }
        },
    }
    
    # Pass through retail moats if available
    enhanced = data.get("enhanced", {})
    moats = enhanced.get("moats", {})
    if moats:
        deal_data["retail_moats"] = moats
    
    return deal_data


def main():
    orch = EnhancedPipelineOrchestrator()
    results = []
    
    for db in DASHBOARDS:
        name = db["name"]
        input_path = db["input"]
        output_dir = db["output_dir"]
        output_file = db["output_file"]
        title = db["title"]
        vercel_url = db["vercel_url"]
        
        print(f"\n{'='*60}")
        print(f"REBUILDING: {name}")
        print(f"  Input:  {input_path}")
        print(f"  Output: {output_dir}/{output_file}")
        print(f"  URL:    {vercel_url}")
        print(f"{'='*60}")
        
        if not os.path.exists(input_path):
            print(f"  ❌ ERROR: Input file not found: {input_path}")
            results.append({"name": name, "status": "ERROR", "url": vercel_url, "error": "Input not found"})
            continue
        
        with open(input_path) as f:
            raw_data = json.load(f)
        
        # Determine format and get deal_data
        if is_pipeline_format(raw_data):
            print(f"  → Pipeline format detected. Extracting deal_data...")
            deal_data = extract_deal_from_pipeline(raw_data)
            print(f"    Extracted: price=${deal_data['property']['price']:,.0f}, "
                  f"sf={deal_data['property']['sf']}, "
                  f"noi=${deal_data['income']['noi']:,.0f}")
        else:
            print(f"  → Analysis format detected. Using directly...")
            deal_data = raw_data
            print(f"    price=${deal_data.get('property',{}).get('price',0):,.0f}, "
                  f"sf={deal_data.get('property',{}).get('sf',0)}")
        
        # Run pipeline
        try:
            result = orch.run_dict(deal_data)
            print(f"  ✓ Pipeline complete")
        except Exception as e:
            print(f"  ❌ Pipeline error: {e}")
            import traceback
            traceback.print_exc()
            results.append({"name": name, "status": "ERROR", "url": vercel_url, "error": str(e)})
            continue
        
        # Verify key sections
        issues = []
        convexity = result.get("convexity", {})
        enhanced = result.get("enhanced", {})
        scenarios = result.get("scenarios", result.get("property_specific_scenarios", {}))
        
        checks = {
            "SCENARIOS": bool(scenarios),
            "DIVERGENCE": bool(convexity.get("divergence")),
            "MOATS": bool(result.get("moats") or enhanced.get("moats")),
            "COMPS": bool(result.get("comps")),
            "OFFERS": bool(result.get("offers") or enhanced.get("offers")),
        }
        for tab, ok in checks.items():
            status = "✓" if ok else "✗ MISSING"
            if not ok:
                issues.append(tab)
            print(f"    {tab}: {status}")
        
        # Generate dashboard
        try:
            html = generate_dashboard(result, title=title)
            print(f"  ✓ Dashboard HTML generated ({len(html):,} bytes)")
        except Exception as e:
            print(f"  ❌ Dashboard generation error: {e}")
            import traceback
            traceback.print_exc()
            results.append({"name": name, "status": "ERROR", "url": vercel_url, "error": f"Dashboard gen: {e}"})
            continue
        
        # Write output
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_file)
        with open(output_path, "w") as f:
            f.write(html)
        print(f"  ✓ Written to {output_path}")
        
        # Save pipeline result for reference
        pipeline_path = os.path.join(output_dir, "pipeline_result.json")
        with open(pipeline_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"  ✓ Pipeline result saved to {pipeline_path}")
        
        status = "FIXED" if not issues else f"FIXED (missing: {', '.join(issues)})"
        results.append({"name": name, "status": status, "url": vercel_url, "issues": issues})
    
    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    for r in results:
        print(f"  {r['name']:25s} | {r['status']:40s} | {r['url']}")
    
    return results


if __name__ == "__main__":
    main()
