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
    .data-row { font-size: 18px !important; font-weight: 900 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. THE RESTORED ENGINE ---
def get_ticker_metrics(ticker):
    try:
        # Quote Data
        q_url = f'https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_KEY}'
        res = requests.get(q_url).json()
        price = res.get('c', 0)
        change = res.get('dp', 0)
        
        # Pull Sentiment & News
        sent_url = f'https://finnhub.io/api/v1/news-sentiment?symbol={ticker}&token={FINNHUB_KEY}'
        s_res = requests.get(sent_url).json()
        s_score = s_res.get('sentiment', {}).get('bullishPercent', 0.5)
        
        # Pull News Headline
        news_url = f'https://finnhub.io/api/v1/company-news?symbol={ticker}&from=2026-03-20&to=2026-03-23&token={FINNHUB_KEY}'
        n_res = requests.get(news_url).json()
        headline = n_res[0].get('headline', '') if n_res else "No recent catalysts found."

        label, css = ("BULLISH", "bullish") if s_score > 0.6 else ("NEUTRAL", "neutral")
        score = int(min(100, max(10, 50 + (change * 5))))
        color = "#FFD700" if score > 80 else "#00ff00" if score > 50 else "#ff3333"
        bar_html = f'<div style="background:#1a1a1a; width:100%; height:12px;"><div style="width:{score}%; background:{color}; height:12px;"></div></div>'
        
        return {
            "ticker": ticker, "price": f"${price:.2f}", "change": f"{change}%", 
            "label": label, "css": css, "bar": bar_html, "score": score, "news": headline
        }
    except: return None

# --- 3. EXPANDED APEX WATCHLIST ---
# Added "Room to Grow" tickers in energy, AI, and biotech
watchlist = [
    "AEMD", "TPET", "MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", 
    "NIO", "WULF", "SERV", "LUNR", "OKLO", "NNE", "SISI", "ZAPP", 
    "KULR", "FFIE", "GWAV", "WKHS", "HOLO", "BTBT", "PTON", "LAES",
    "CAN", "ANY", "MIGI", "GREE", "VLD", "QUBT" # Look-alike small caps
]

results = []
for t in watchlist:
    m = get_ticker_metrics(t)
    if m:
        p_val = float(m['price'].replace('$', ''))
        # Slightly wider filter to ensure we hit 20 stocks
        if 1.00 <= p_val <= 35.0:
            results.append(m)

# UI RENDER
st.title(f"🔮 APEX ORACLE: MASTER COMMAND CENTER")
st.markdown('<div class="oracle-grid header-row"><div>Ticker</div><div>Price</div><div>Change</div><div>Sentiment</div><div>Strength</div><div>Signal</div></div>', unsafe_allow_html=True)

top_20 = sorted(results, key=lambda x: x['score'], reverse=True)[:20]

for d in top_20:
    sig = "🔥 GOLD" if d['score'] >= 80 else "⚡ ACTIVE"
    st.markdown(f"""
        <div class="oracle-grid data-row">
            <div style="color:#00ffcc;">{d['ticker']}</div>
            <div>{d['price']}</div>
            <div style="color:{'#00ff00' if '-' not in d['change'] else '#ff3333'};">{d['change']}</div>
            <div><span class="sentiment-tag {d['css']}">{d['label']}</span></div>
            <div>{d['bar']}</div>
            <div style="font-size:12px; color:{'#FFD700' if 'GOLD' in sig else '#444'};">{sig}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br><h3>📰 PRO CATALYST FEED</h3>", unsafe_allow_html=True)
for d in top_20:
    if d['news'] != "No recent catalysts found.":
        st.markdown(f"""
            <div style="background:#0a0a0a; padding:12px; border-left:4px solid #00ffcc; margin-bottom:8px;">
                <b style="color:#00ffcc;">{d['ticker']}</b> | <span class="sentiment-tag {d['css']}">{d['label']}</span><br>
                <span style="font-size:14px;">{d['news']}</span>
            </div>
        """, unsafe_allow_html=True)
