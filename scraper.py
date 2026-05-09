#!/usr/bin/env python3
"""Scrape ALL NJ LoopNet listings via Firefox remote debugging."""
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import time, re, os, csv, json

SAVE_DIR = os.path.expanduser("~/cre/incoming/nj-full")
os.makedirs(SAVE_DIR, exist_ok=True)

options = Options()
options.debugger_address = "127.0.0.1:9222"
driver = webdriver.Firefox(options=options)

BASE = "https://www.loopnet.com/search/commercial-real-estate/nj/for-sale/"
all_listings = []
MAX_PAGES = 35

for page_num in range(1, MAX_PAGES + 1):
    url = BASE if page_num == 1 else f"{BASE}{page_num}/"
    print(f"\nPAGE {page_num}: {url}")
    
    driver.get(url)
    time.sleep(3.5)
    
    html = driver.page_source
    fname = os.path.join(SAVE_DIR, f"nj_page{page_num}.html")
    with open(fname, 'w') as f:
        f.write(html)
    
    soup = BeautifulSoup(html, 'lxml')
    placards = soup.select('article.placard')
    
    page_listings = 0
    for card in placards:
        data_id = card.get('data-id', '')
        if not data_id:
            continue
        
        city = card.get('gtm-listing-city', '')
        state = card.get('gtm-listing-state', '')
        if state != 'NJ':
            continue
        
        prop_type = card.get('gtm-listing-property-type-name', '')
        title_el = card.select_one('h4 a, h5 a')
        title = title_el.get_text(strip=True) if title_el else ''
        sub_el = card.select_one('h6 a')
        subtitle = sub_el.get_text(strip=True) if sub_el else ''
        card_text = card.get_text(' ', strip=True)
        
        price = ''
        pm = re.search(r'Starting\s+bid\s+(\$[\d,]+)', card_text)
        if not pm:
            pm = re.search(r'(?<!\w)(\$\d[\d,]{2,}(?:,\d{3})*)', card_text)
        if pm:
            price = pm.group(1)
        
        sf = ''
        pm = re.search(r'([\d,]+)\s*SF', card_text)
        if pm:
            sf = pm.group(1)
        
        all_listings.append({
            'page': page_num, 'id': data_id, 'title': title[:150],
            'subtitle': subtitle[:200], 'address': f"{city}, {state}",
            'city': city, 'state': state, 'type': prop_type,
            'price': price, 'sf': sf,
        })
        page_listings += 1
    
    print(f"  Saved: {len(html):,} chars | NJ listings: {page_listings}")
    
    # Check for next page
    next_link = soup.select_one('a[aria-label="Go to next page"]')
    if page_num > 1 and not next_link:
        print(f"  No next page — stopping")
        break
    
    time.sleep(1.5)

# Save
csv_path = os.path.join(SAVE_DIR, "nj_all_listings.csv")
json_path = os.path.join(SAVE_DIR, "nj_all_listings.json")

with open(csv_path, 'w', newline='') as f:
    fields = ['page','id','title','subtitle','address','city','state','type','price','sf']
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(all_listings)

with open(json_path, 'w') as f:
    json.dump(all_listings, f, indent=2)

print(f"\n{'='*60}")
print(f"DONE: {len(all_listings)} NJ listings across {page_num} pages")
print(f"CSV: {csv_path}")
print(f"JSON: {json_path}")

driver.quit()
