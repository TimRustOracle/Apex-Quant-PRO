import streamlit as st
import requests
import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. CORE CONFIG ---
st.set_page_config(layout="wide", page_title="APEX COMMAND CENTER")
st_autorefresh(interval=60000, key="oracle_pulse")

AV_KEY = "VNHELWLTQGHT0IYT" 
FINNHUB_KEY = "d70n0i9r01ql6rnvssl0d70n0i9r01ql6rnvsslg"

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #fff; }
    .oracle-grid { display: grid; grid-template-columns: 100px 100px 100px 120px 1fr 100px; gap: 15px; align-items: center; padding: 10px; border-bottom: 1px solid #222; }
    .header-row { background-color: #111; color: #00ffcc; font-weight: bold; text-transform: uppercase; border-bottom: 2px solid #333; }
    .sentiment-tag { padding: 2px 6px; border-radius: 3px; font-size: 11px; font-weight: bold; }
    .bullish { background: #004d00; color: #00ff00; }
    .neutral { background: #333; color: #aaa; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DYNAMIC DISCOVERY ENGINE ---
@st.cache_data(ttl=300)
def discover_active_stocks():
    """Finds the top moving stocks in the market to ensure the list is always 20."""
    try:
        # Fetching top gainers/actives from Alpha Vantage
        url = f'https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey={AV_KEY}'
        data = requests.get(url).json()
        
        # Combine gainers and most active for a broad pool
        pool = data.get('top_gainers', []) + data.get('most_actively_traded', [])
        
        discovered = []
        for item in pool:
            ticker = item['ticker']
            price = float(item['price'])
            # FILTER: Your specific $2 - $25 strategy
            if 2.0 <= price <= 25.0:
                discovered.append(ticker)
        
        # Add your core "Must-Watch" tickers to the pool
        core_watchlist = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "TPET"]
        return list(set(core_watchlist + discovered))[:20] # Return exactly 20
    except:
        return ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "WULF"]

def get_ticker_metrics(ticker):
    try:
        url = f'https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_KEY}'
        res = requests.get(url).json()
        price = res.get('c', 0)
        change = res.get('dp', 0)
        
        # Pull Sentiment
        sent_url = f'https://finnhub.io/api/v1/news-sentiment?symbol={ticker}&token={FINNHUB_KEY}'
        s_res = requests.get(sent_url).json()
        s_score = s_res.get('sentiment', {}).get('bullishPercent', 0.5)
        
        label, css = ("BULLISH", "bullish") if s_score > 0.6 else ("NEUTRAL", "neutral")
        score = int(min(100, max(10, 50 + (change * 5))))
        bar_html = f'<div style="background:#1a1a1a; width:100%; height:12px;"><div style="width:{score}%; background:{"#FFD700" if score > 80 else "#00ff00"}; height:12px;"></div></div>'
        
        return {"ticker": ticker, "price": f"${price:.2f}", "change": f"{change}%", "label": label, "css": css, "bar": bar_html, "score": score}
    except: return None

# --- 3. EXECUTION ---
st.title("🔮 APEX ORACLE: DYNAMIC 20")
active_list = discover_active_stocks()

results = []
for t in active_list:
    m = get_ticker_metrics(t)
    if m: results.append(m)

# UI RENDER
st.markdown('<div class="oracle-grid header-row"><div>Ticker</div><div>Price</div><div>Change</div><div>Sentiment</div><div>Strength</div><div>Signal</div></div>', unsafe_allow_html=True)
for d in sorted(results, key=lambda x: x['score'], reverse=True):
    sig = "🔥 GOLD" if d['score'] >= 80 else "⚡ ACTIVE"
    st.markdown(f"""
        <div class="oracle-grid">
            <div style="color:#00ffcc; font-weight:bold;">{d['ticker']}</div>
            <div>{d['price']}</div>
            <div style="color:{'#00ff00' if '-' not in d['change'] else '#ff3333'};">{d['change']}</div>
            <div><span class="sentiment-tag {d['css']}">{d['label']}</span></div>
            <div>{d['bar']}</div>
            <div style="font-size:12px; color:{'#FFD700' if 'GOLD' in sig else '#444'};">{sig}</div>
        </div>
    """, unsafe_allow_html=True)
