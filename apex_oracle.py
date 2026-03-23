import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import time
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & SYSTEM CLOCK ---
st.set_page_config(layout="wide", page_title="APEX ORACLE COMMAND")
st_autorefresh(interval=30000, key="oracle_pulse")

# Live Clock display for the top bar
current_time = datetime.datetime.now().strftime("%H:%M:%S")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #000; color: #fff; font-family: 'Arial', sans-serif; }}
    .top-bar {{ display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 2px solid #00ffcc; margin-bottom: 20px; }}
    .live-clock {{ font-size: 24px; font-weight: 900; color: #00ffcc; }}
    .oracle-grid {{ display: grid; grid-template-columns: 120px 100px 100px 1fr 120px; gap: 15px; align-items: center; padding: 10px; border-bottom: 1px solid #222; }}
    .header-row {{ background-color: #111; color: #00ffcc !important; font-weight: bold; font-size: 13px; text-transform: uppercase; border-bottom: 2px solid #333; position: sticky; top: 0; z-index: 99; }}
    .data-row {{ font-size: 20px !important; font-weight: 900 !important; }}
    .bar-bg {{ background: #1a1a1a; border-radius: 4px; width: 100%; height: 16px; border: 1px solid #333; }}
    .bar-fill {{ height: 16px; border-radius: 3px; transition: width 0.8s ease-in-out; }}
    .news-card {{ background: #0a0a0a; padding: 12px; border-left: 4px solid #00ffcc; margin-bottom: 8px; font-size: 14px; }}
    </style>
    <div class="top-bar">
        <div style="font-size: 28px; font-weight: 900;">🔮 APEX ORACLE: COMMAND CENTER</div>
        <div class="live-clock">🕒 {current_time}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 2. THE DYNAMIC SCANNER ENGINE ---
def get_oracle_data(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="3d", interval="5m")
        if df.empty or len(df) < 15: return None
        
        price = float(df['Close'].iloc[-1])
        # STRICT DAY TRADING PARAMETERS ($2 - $20)
        if not (2.0 <= price <= 20.0): return None

        curr_vol = df['Volume'].iloc[-1]
        avg_vol = df['Volume'].mean()
        vol_mult = round(curr_vol / avg_vol, 1) if avg_vol > 0 else 1.0

        ema = df['Close'].ewm(span=9).mean().iloc[-1]
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = 100 - (100 / (1 + (gain / loss))) if loss != 0 else 50
        
        # Scoring logic heavily weights price action vs EMA and Volume
        score = int(round((rsi * 0.4) + (((price - ema) / ema) * 2000) + (vol_mult * 10), 0))
        score = min(100, max(5, score))
        
        color = "#FFD700" if score >= 85 else "#00ff00" if score >= 60 else "#ff3333"
        bar_html = f'<div class="bar-bg"><div class="bar-fill" style="width: {score}%; background: {color};"></div></div>'
        
        # News
        news_list = []
        if t.news:
            for n in t.news[:1]:
                news_list.append({'pub': n.get('publisher', 'Market'), 'title': n.get('title', '')})

        return {
            "ticker": ticker, "price": f"${price:.2f}", "vol_mult": f"{vol_mult}x",
            "bar": bar_html, "score": score, "news": news_list
        }
    except: return None

# --- 3. DYNAMIC POOL & RENDERING ---
# Broad list of small-cap tickers to scan
deep_scan_pool = [
    "MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", 
    "TPST", "TPET", "BTBT", "MSTR", "CAN", "WULF", "CLEU", "BXRX", "AEMD", "SERV",
    "LUNR", "OKLO", "NNE", "SISI", "ZAPP", "AEI", "KULR", "TTOO", "FFIE", "GWAV",
    "PTON", "AADI", "LAES", "TCBP", "OCEA", "ADTX", "VERV", "BNGO", "WKHS", "NKLA"
]

all_results = []
for ticker in deep_scan_pool:
    data = get_oracle_data(ticker)
    if data: all_results.append(data)

# Sort and slice to get exactly the top 20 strongest
top_20 = sorted(all_results, key=lambda x: x['score'], reverse=True)[:20]

# UI Grid
st.markdown('<div class="oracle-grid header-row"><div>TICKER</div><div>PRICE</div><div>VOL X</div><div>STRENGTH</div><div>SIGNAL</div></div>', unsafe_allow_html=True)

final_news = []
for d in top_20:
    sig = "🔥 GOLD" if d['score'] >= 85 else "⚡ ACTIVE"
    st.markdown(f"""
        <div class="oracle-grid data-row">
            <div><a href="https://www.tradingview.com/chart/?symbol={d['ticker']}" target="_blank" style="color:#00ffcc; text-decoration:none;">{d['ticker']}</a></div>
            <div>{d['price']}</div>
            <div style="color: {'#00ff00' if float(d['vol_mult'][:-1]) > 1.2 else '#555'};">{d['vol_mult']}</div>
            <div>{d['bar']}</div>
            <div style="font-size:14px; color:{'#FFD700' if 'GOLD' in sig else '#555'};">{sig}</div>
        </div>
        """, unsafe_allow_html=True)
    final_news.extend(d['news'])

# Global News Feed
st.markdown("<br><br><h3>📰 SYSTEM CATALYSTS</h3>", unsafe_allow_html=True)
if final_news:
    for n in final_news[:10]:
        st.markdown(f'<div class="news-card"><b>{n["pub"]}</b>: {n["title"]}</div>', unsafe_allow_html=True)
