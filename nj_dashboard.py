import streamlit as st
import pandas as pd
import os
import re

st.set_page_config(
    page_title="NJ CRE Pipeline",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Theme ──
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background: #08090a;
    }
    
    /* Card styling */
    .property-card {
        background: #191a1b;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        padding: 18px 20px;
        margin-bottom: 8px;
        transition: all 0.15s;
    }
    .property-card:hover {
        border-color: rgba(255,255,255,0.14);
        background: #23252a;
    }
    
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 8px;
    }
    .card-num {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #62666d;
    }
    .card-type {
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #8a8f98;
    }
    .card-address {
        font-size: 15px;
        font-weight: 510;
        color: #f7f8f8;
        margin-bottom: 2px;
    }
    .card-city {
        font-size: 12px;
        color: #8a8f98;
        margin-bottom: 6px;
    }
    .card-subtitle {
        font-size: 12px;
        color: #8a8f98;
        line-height: 1.4;
        margin-bottom: 8px;
    }
    
    .card-stats {
        display: flex;
        gap: 24px;
        padding-top: 8px;
        border-top: 1px solid rgba(255,255,255,0.05);
    }
    .stat-label {
        font-size: 10px;
        font-weight: 500;
        color: #62666d;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .stat-value {
        font-size: 16px;
        font-weight: 590;
        color: #f7f8f8;
    }
    .stat-value.price {
        color: #7170ff;
    }
    
    /* Search */
    .stTextInput > div > div > input {
        background: #191a1b !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        color: #f7f8f8 !important;
        border-radius: 6px !important;
    }
    
    /* Metric cards */
    div[data-testid="stMetricValue"] {
        color: #f7f8f8 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        color: #d0d6e0 !important;
        border-radius: 6px !important;
        font-size: 12px !important;
    }
    .stButton > button:hover {
        background: rgba(255,255,255,0.08) !important;
        border-color: rgba(255,255,255,0.14) !important;
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        background: #191a1b !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        color: #f7f8f8 !important;
    }
    
    ::-webkit-scrollbar {width: 6px;}
    ::-webkit-scrollbar-track {background: #08090a;}
    ::-webkit-scrollbar-thumb {background: #333; border-radius: 3px;}
</style>
""", unsafe_allow_html=True)

# ── Load data ──
@st.cache_data(ttl=3600)
def load_data():
    # Try relative path first (Streamlit Cloud), then absolute (local dev)
    paths = [
        os.path.join(os.path.dirname(__file__), "data.csv"),
        os.path.expanduser("~/cre/incoming/nj-full/nj_all_listings.csv"),
    ]
    for p in paths:
        if os.path.exists(p):
            df = pd.read_csv(p)
            break
    else:
        st.error("No data file found. Run scraper first.")
        return pd.DataFrame()
    
    # Parse price numbers
    def parse_price(p):
        if pd.isna(p) or str(p).strip() == '' or p == 'N/A':
            return None
        m = re.search(r'\$([\d,]+)', str(p))
        return int(m.group(1).replace(',','')) if m else None
    
    df['price_num'] = df['price'].apply(parse_price)
    df['sf_num'] = pd.to_numeric(df['sf'].str.replace(',',''), errors='coerce').fillna(0).astype(int)
    df['price_per_sf'] = df.apply(
        lambda r: int(round(r['price_num'] / r['sf_num'])) if pd.notna(r['price_num']) and r['sf_num'] > 0 else None, axis=1
    )
    df = df.sort_values('price_num', na_position='last').reset_index(drop=True)
    df['num'] = range(1, len(df) + 1)
    return df

df = load_data()

if df.empty:
    st.warning("Scraping in progress — data will appear once complete. Refresh in ~2 minutes.")
    st.stop()

# ── Header ──
st.title("NJ CRE Pipeline")
st.caption(f"LoopNet · NJ for-sale · {len(df)} listings · {df['city'].nunique()} cities")

# ── KPI Row ──
with_price = df[df['price_num'].notna()]
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Listings", len(df))
k2.metric("With Price", f"{len(with_price)} ({len(with_price)/len(df)*100:.0f}%)")
k3.metric("Median Price", f"${with_price['price_num'].median():,.0f}" if len(with_price) > 0 else "N/A")
k4.metric("Price Range", f"${with_price['price_num'].min():,.0f} — ${with_price['price_num'].max():,.0f}" if len(with_price) > 0 else "N/A")
k5.metric("Cities", df['city'].nunique())

# ── Filters ──
c1, c2, c3 = st.columns([3, 2, 2])
with c1:
    search = st.text_input("Search", placeholder="Address, city, or description...", label_visibility="collapsed")
with c2:
    types = ['All'] + sorted(df['type'].dropna().unique().tolist())
    type_filter = st.selectbox("Type", types, label_visibility="collapsed")
with c3:
    sorts = ['Price ↑', 'Price ↓', 'SF ↓', 'City A-Z', 'Type']
    sort_by = st.selectbox("Sort", sorts, label_visibility="collapsed")

# ── Filter logic ──
filtered = df.copy()
if search:
    q = search.lower()
    mask = (
        filtered['title'].str.lower().str.contains(q, na=False) |
        filtered['city'].str.lower().str.contains(q, na=False) |
        filtered['address'].str.lower().str.contains(q, na=False) |
        filtered['subtitle'].str.lower().str.contains(q, na=False)
    )
    filtered = filtered[mask]
if type_filter != 'All':
    filtered = filtered[filtered['type'] == type_filter]

if sort_by == 'Price ↑':
    filtered = filtered.sort_values('price_num', na_position='last')
elif sort_by == 'Price ↓':
    filtered = filtered.sort_values('price_num', ascending=False, na_position='last')
elif sort_by == 'SF ↓':
    filtered = filtered.sort_values('sf_num', ascending=False)
elif sort_by == 'City A-Z':
    filtered = filtered.sort_values('city')
elif sort_by == 'Type':
    filtered = filtered.sort_values(['type', 'price_num'], na_position='last')

filtered = filtered.reset_index(drop=True)

st.caption(f"Showing {len(filtered)} of {len(df)} listings")

# ── Listing Cards ──
for _, row in filtered.iterrows():
    price_str = row['price'] if pd.notna(row['price']) and row['price'] != '' else 'N/A'
    sf_str = f"{row['sf_num']:,} SF" if row['sf_num'] > 0 else '—'
    ppsf = f"${row['price_per_sf']:,}/SF" if row.get('price_per_sf') else '—'
    
    card_html = f"""
    <div class="property-card">
        <div class="card-header">
            <div>
                <div class="card-type">{row['type']}</div>
                <div class="card-address">{row['title']}</div>
                <div class="card-city">{row['address']}</div>
                <div class="card-subtitle">{row['subtitle'] if pd.notna(row['subtitle']) else ''}</div>
            </div>
            <div class="card-num">#{int(row['num'])}</div>
        </div>
        <div class="card-stats">
            <div><div class="stat-label">Price</div><div class="stat-value price">{price_str}</div></div>
            <div><div class="stat-label">Size</div><div class="stat-value">{sf_str}</div></div>
            <div><div class="stat-label">$/SF</div><div class="stat-value">{ppsf}</div></div>
            <div><div class="stat-label">City</div><div class="stat-value" style="font-size:14px;">{row['city']}</div></div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

# ── Sidebar: Deep Dive ──
with st.sidebar:
    st.header("Deep Dive")
    selected = st.number_input("Listing #", min_value=1, max_value=len(df), step=1)
    if st.button("Analyze Selected"):
        listing = df[df['num'] == selected]
        if not listing.empty:
            row = listing.iloc[0]
            st.success(f"Deep dive #{selected}")
            st.write(f"**{row['title']}**")
            st.write(f"{row['address']}")
            st.write(f"Type: {row['type']}")
            st.write(f"Price: {row['price']}")
            st.write(f"SF: {row['sf']}")
            st.write(f"ID: {row['id']}")
