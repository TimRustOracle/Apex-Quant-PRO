import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & PRO-STYLING ---
st.set_page_config(layout="wide", page_title="APEX ORACLE")
st_autorefresh(interval=60000, key="oracle_pulse") # Refresh every 60s for stability

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #fff; font-family: 'Arial', sans-serif; }
    .oracle-grid { display: grid; grid-template-columns: 120px 120px 1fr 120px; gap: 15px; align-items: center; padding: 10px; border-bottom: 1px solid #222; }
    .header-row { background-color: #111; color: #00ffcc !important; font-weight: bold; font-size: 13px; text-transform: uppercase; border-bottom: 2px solid #333; position: sticky; top: 0; z-index: 100; }
    .data-row { font-size: 20px !important; font-weight: 900 !important; }
    .bar-bg { background: #1a1a1a; border-radius: 4px; width: 100%; height: 14px; border: 1px solid #333; }
    .bar-fill { height: 14px; border-radius: 3px; transition: width 0.8s ease-in-out; }
    .news-card { background: #0a0a0a; padding: 12px; border-left: 4px solid #00ffcc; margin-bottom: 8px; border-radius: 4px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE DYNAMIC ENGINE ---
def get_stock_data(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="2d", interval="5m")
        if df.empty or len(df) < 20: return None
        
        price = float(df['Close'].iloc[-1])
        # STRICT CRITERIA: $2 - $20
        if not (2.0 <= price <= 20.0): return None

        # EMA & RSI Logic
        ema = df['Close'].ewm(span=9).mean().iloc[-1]
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = 100 - (100 / (1 + (gain / loss))) if loss != 0 else 50
        
        # Strength Score calculation
        score = int(round((rsi * 0.5) + (((price - ema) / ema) * 1500), 0))
        score = min(100, max(5, score))
        
        color = "#FFD700" if score >= 80 else "#00ff00" if score >= 55 else "#ff3333"
        bar_html = f'<div class="bar-bg"><div class="bar-fill" style="width: {score}%; background: {color};"></div></div>'
        
        # News handling with safer extraction to prevent KeyError
        news_items = []
        raw_news = t.news[:2] if t.news else []
        for n in raw_news:
            news_items.append({'pub': n.get('publisher', 'Market'), 'title': n.get('title', 'Headline')})

        return {
            "ticker": ticker, "price": price, "price_str": f"${price:.2f}",
            "bar": bar_html, "score": score, "news": news_items
        }
    except: return None

# --- 3. THE DASHBOARD ---
st.title("🔮 APEX ORACLE: TOP 20 RUNNERS")

# Wider scan pool of common small-cap/mid-cap runners
scan_pool = [
    "MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", 
    "TPST", "TPET", "BTBT", "MSTR", "CAN", "WULF", "CLEU", "BXRX", "AEMD", "SERV",
    "LUNR", "OKLO", "NNE", "SISI", "ZAPP", "AEI", "KULR", "TTOO", "FFIE", "GWAV"
]

all_data = []
for t in scan_pool:
    data = get_stock_data(t)
    if data: all_data.append(data)

# SORT BY SCORE (Strongest first) and take TOP 20
top_20 = sorted(all_data, key=lambda x: x['score'], reverse=True)[:20]

# --- UI RENDER ---
st.markdown('<div class="oracle-grid header-row"><div>TICKER</div><div>PRICE</div><div>STRENGTH</div><div>SIGNAL</div></div>', unsafe_allow_html=True)

catalysts = []
for d in top_20:
    signal = "🔥 GOLD" if d['score'] >= 80 else "⚡ ACTIVE"
    st.markdown(f"""
        <div class="oracle-grid data-row">
            <div><a href="https://www.tradingview.com/chart/?symbol={d['ticker']}" target="_blank" style="color:#00ffcc; text-decoration:none;">{d['ticker']}</a></div>
            <div>{d['price_str']}</div>
            <div>{d['bar']}</div>
            <div style="font-size:14px; color:{'#FFD700' if 'GOLD' in signal else '#555'};">{signal}</div>
        </div>
        """, unsafe_allow_html=True)
    if d['news']: catalysts.extend(d['news'])

st.markdown("<br><br>", unsafe_allow_html=True)
st.subheader("📰 LIVE CATALYST FEED")

if catalysts:
    # Remove duplicate headlines and show top 10
    seen = set()
    for n in catalysts[:15]:
        if n['title'] not in seen:
            st.markdown(f'<div class="news-card"><b>{n["pub"]}</b>: {n["title"]}</div>', unsafe_allow_html=True)
            seen.add(n['title'])
else:
    st.info("Searching for fresh catalysts...")
