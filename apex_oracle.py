import streamlit as st
import requests
import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. CORE CONFIG ---
st.set_page_config(layout="wide", page_title="APEX COMMAND CENTER")
st_autorefresh(interval=30000, key="oracle_pulse") # 30s Turbo Refresh

AV_KEY = "VNHELWLTQGHT0IYT" 
FINNHUB_KEY = "d70n0i9r01ql6rnvssl0d70n0i9r01ql6rnvsslg"

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #fff; }
    .oracle-grid { display: grid; grid-template-columns: 100px 90px 90px 80px 100px 1fr 100px; gap: 12px; align-items: center; padding: 10px; border-bottom: 1px solid #222; }
    .header-row { background-color: #111; color: #00ffcc; font-weight: bold; text-transform: uppercase; border-bottom: 2px solid #333; font-size: 12px; }
    .tv-link { color: #00ffcc !important; text-decoration: none; border: 1px solid #00ffcc; padding: 2px 6px; border-radius: 4px; font-size: 14px; }
    .tv-link:hover { background: #00ffcc; color: #000 !important; }
    .sentiment-tag { padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold; }
    .bullish { background: #004d00; color: #00ff00; }
    .neutral { background: #333; color: #aaa; }
    .rvol-high { color: #FFD700; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. THE ADVANCED DATA ENGINE ---
def get_apex_metrics(ticker):
    try:
        # 1. Real-time Price & Change (Finnhub)
        q_url = f'https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_KEY}'
        q_res = requests.get(q_url).json()
        price = q_res.get('c', 0)
        change = q_res.get('dp', 0)
        curr_vol = q_res.get('v', 0)

        # 2. RVOL Calculation (Sourced from Alpha Vantage Overview)
        # RVOL = Current Volume / Avg Daily Volume
        ov_url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={AV_KEY}'
        ov_res = requests.get(ov_url).json()
        avg_vol = float(ov_res.get('AverageDailyVolume10Day', 1))
        rvol = round(curr_vol / avg_vol, 2) if curr_vol > 0 else 0.0

        # 3. Sentiment & News
        sent_url = f'https://finnhub.io/api/v1/news-sentiment?symbol={ticker}&token={FINNHUB_KEY}'
        s_res = requests.get(sent_url).json()
        s_score = s_res.get('sentiment', {}).get('bullishPercent', 0.5)
        
        news_url = f'https://finnhub.io/api/v1/company-news?symbol={ticker}&from=2026-03-21&to=2026-03-23&token={FINNHUB_KEY}'
        n_res = requests.get(news_url).json()
        headline = n_res[0].get('headline', '') if n_res else ""

        # --- 4. TRIPLE-THREAT LOGIC ---
        is_gold = (change > 5.0) and (s_score > 0.6) and (len(headline) > 0)
        label, css = ("BULLISH", "bullish") if s_score > 0.6 else ("NEUTRAL", "neutral")
        
        score = int(min(100, max(10, 50 + (change * 5) + (rvol * 5))))
        color = "#FFD700" if is_gold else "#00ff00" if score > 50 else "#ff3333"
        bar_html = f'<div style="background:#1a1a1a; width:100%; height:10px;"><div style="width:{score}%; background:{color}; height:10px;"></div></div>'
        
        return {
            "ticker": ticker, "price": f"${price:.2f}", "change": f"{change}%", "rvol": rvol,
            "label": label, "css": css, "bar": bar_html, "score": score, "news": headline, "gold": is_gold
        }
    except: return None

# --- 3. UI RENDER ---
st.title("🔮 APEX ORACLE: COMMAND CENTER v78")

# Force Refresh Button
if st.sidebar.button("🔄 FORCE REFRESH"):
    st.rerun()

watchlist = ["AEMD", "TPET", "MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "WULF", "SERV", "LUNR", "OKLO", "NNE", "SISI", "ZAPP", "KULR", "FFIE", "GWAV", "WKHS", "HOLO", "BTBT", "PTON", "LAES", "CAN", "ANY", "MIGI", "GREE", "VLD", "QUBT"]

results = []
for t in watchlist[:20]: # Processing top 20 to respect API rate limits
    m = get_apex_metrics(t)
    if m: results.append(m)

# UI GRID
st.markdown('<div class="oracle-grid header-row"><div>Ticker</div><div>Price</div><div>Change</div><div>RVOL</div><div>Sentiment</div><div>Strength</div><div>Signal</div></div>', unsafe_allow_html=True)

for d in sorted(results, key=lambda x: x['score'], reverse=True):
    sig = "🔥 GOLD" if d['gold'] else "⚡ ACTIVE"
    tv_url = f"https://www.tradingview.com/chart/?symbol={d['ticker']}"
    rvol_class = "rvol-high" if d['rvol'] > 2.0 else ""
    
    st.markdown(f"""
        <div class="oracle-grid">
            <div><a href="{tv_url}" target="_blank" class="tv-link">{d['ticker']}</a></div>
            <div style="font-weight:bold;">{d['price']}</div>
            <div style="color:{'#00ff00' if '-' not in d['change'] else '#ff3333'};">{d['change']}</div>
            <div class="{rvol_class}">{d['rvol']}x</div>
            <div><span class="sentiment-tag {d['css']}">{d['label']}</span></div>
            <div>{d['bar']}</div>
            <div style="font-size:12px; color:{'#FFD700' if d['gold'] else '#444'};">{sig}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br><h3>📰 PRO CATALYST FEED</h3>", unsafe_allow_html=True)
for d in results:
    if d['news']:
        st.markdown(f'<div style="background:#0a0a0a; padding:10px; border-left:4px solid #00ffcc; margin-bottom:5px;"><b>{d["ticker"]}</b>: {d["news"]}</div>', unsafe_allow_html=True)
