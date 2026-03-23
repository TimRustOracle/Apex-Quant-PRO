import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & GRID STYLING ---
st.set_page_config(layout="wide", page_title="APEX ORACLE")
st_autorefresh(interval=30000, key="oracle_pulse")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #fff; font-family: 'Arial', sans-serif; }
    
    /* Fixed-Width Row for Perfect Header Alignment */
    .oracle-grid {
        display: grid;
        grid-template-columns: 150px 150px 1fr 150px;
        gap: 15px;
        align-items: center;
        padding: 12px;
        border-bottom: 1px solid #222;
    }
    
    .header-row {
        background-color: #111;
        color: #00ffcc !important;
        font-weight: bold;
        font-size: 14px;
        text-transform: uppercase;
        border-bottom: 2px solid #333;
    }

    .data-row { font-size: 22px !important; font-weight: 900 !important; }
    
    /* Bar Styling */
    .bar-bg { background: #1a1a1a; border-radius: 6px; width: 100%; height: 16px; border: 1px solid #333; }
    .bar-fill { height: 16px; border-radius: 5px; transition: width 0.8s ease-in-out; }
    
    /* News Section Styling */
    .news-container { margin-top: 40px; border-top: 2px solid #00ffcc; padding-top: 20px; }
    .news-card { background: #0a0a0a; padding: 15px; border-left: 5px solid #00ffcc; margin-bottom: 10px; border-radius: 0 5px 5px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE ---
def get_oracle_data(ticker):
    try:
        t = yf.Ticker(ticker)
        # Fetch data and handle multi-index structure often found in yfinance
        df = t.history(period="1d", interval="5m")
        if df.empty: return None
        
        price = float(df['Close'].iloc[-1])
        volume = t.info.get('regularMarketVolume', 0)
        
        # --- STICK TO YOUR TRADING PARAMETERS ($2-$20) ---
        if not (2.0 <= price <= 20.0) or volume < 100000:
            return None

        ema = df['Close'].ewm(span=9).mean().iloc[-1]
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = 100 - (100 / (1 + (gain / loss))) if loss != 0 else 50
        
        # Apex Strength Score
        score = int(round((rsi * 0.5) + (((price - ema) / ema) * 1500), 0))
        score = min(100, max(5, score))
        
        # Gold Zone Logic
        color = "#FFD700" if score >= 80 else "#00ff00" if score >= 55 else "#ff3333"
        bar_html = f'<div class="bar-bg"><div class="bar-fill" style="width: {score}%; background: {color};"></div></div>'
        
        return {
            "ticker": ticker, 
            "price": f"${price:.2f}", 
            "bar": bar_html, 
            "news": t.news[:3],
            "score": score
        }
    except: return None

# --- 3. THE DASHBOARD ---
st.title("🔮 APEX ORACLE: COMMAND CENTER")

# Section 1: The Scanner
st.subheader("📡 SCANNER (FILTERED: $2-$20)")
st.markdown("""
    <div class="oracle-grid header-row">
        <div>TICKER</div>
        <div>PRICE</div>
        <div>STRENGTH BAR</div>
        <div>STATUS</div>
    </div>
    """, unsafe_allow_html=True)

watchlist = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST", "TPET", "BTBT", "MSTR"]
all_catalysts = []

for t in watchlist:
    data = get_oracle_data(t)
    if data:
        status_text = "🔥 GOLD" if data['score'] >= 80 else "⚡ ACTIVE"
        st.markdown(f"""
            <div class="oracle-grid data-row">
                <div><a href="https://www.tradingview.com/chart/?symbol={data['ticker']}" target="_blank" style="color:#00ffcc; text-decoration:none;">{data['ticker']}</a></div>
                <div>{data['price']}</div>
                <div>{data['bar']}</div>
                <div style="font-size:14px; color:{'#FFD700' if 'GOLD' in status_text else '#555'};">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)
        all_catalysts.extend(data['news'])

# Section 2: The News (Below the Scanner)
st.markdown('<div class="news-container">', unsafe_allow_html=True)
st.subheader("📰 LIVE CATALYST & SENTIMENT FEED")

if not all_catalysts:
    st.write("No major catalysts for filtered tickers in the last 24h.")
else:
    for n in all_catalysts:
        st.markdown(f"""
            <div class="news-card">
                <span style="color:#00ffcc; font-weight:bold;">{n.get('publisher', 'News')}</span> | {n['title']}<br>
                <a href="{n['link']}" target="_blank" style="color:#555; font-size:12px;">View Source</a>
            </div>
            """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
