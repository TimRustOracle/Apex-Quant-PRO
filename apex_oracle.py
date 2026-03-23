import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & SYSTEM CLOCK ---
st.set_page_config(layout="wide", page_title="APEX ORACLE COMMAND")
st_autorefresh(interval=30000, key="oracle_pulse")

current_time = datetime.datetime.now().strftime("%H:%M:%S")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #000; color: #fff; font-family: 'Arial', sans-serif; }}
    .top-bar {{ display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 2px solid #00ffcc; margin-bottom: 10px; }}
    .live-clock {{ font-size: 22px; font-weight: 900; color: #00ffcc; }}
    .oracle-grid {{ display: grid; grid-template-columns: 120px 100px 100px 100px 1fr 120px; gap: 15px; align-items: center; padding: 10px; border-bottom: 1px solid #222; }}
    .header-row {{ background-color: #111; color: #00ffcc !important; font-weight: bold; font-size: 13px; text-transform: uppercase; border-bottom: 2px solid #333; }}
    .data-row {{ font-size: 18px !important; font-weight: 900 !important; }}
    .bar-bg {{ background: #1a1a1a; border-radius: 4px; width: 100%; height: 16px; border: 1px solid #333; }}
    .bar-fill {{ height: 16px; border-radius: 3px; transition: width 0.8s ease-in-out; }}
    .catalyst-card {{ background: #0a0a0a; padding: 12px; border-left: 5px solid #00ffcc; margin-bottom: 8px; border-radius: 0 4px 4px 0; }}
    .tag {{ padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold; margin-right: 8px; }}
    .bullish {{ background: #004d00; color: #00ff00; }}
    .bearish {{ background: #4d0000; color: #ff3333; }}
    </style>
    <div class="top-bar">
        <div style="font-size: 24px; font-weight: 900;">🔮 APEX ORACLE: COMMAND CENTER</div>
        <div class="live-clock">🕒 {current_time}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE ---
def get_data(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="2d", interval="5m")
        if df.empty: return None
        
        price = float(df['Close'].iloc[-1])
        # Filter: $2 - $20
        if not (2.0 <= price <= 20.0): return None
        
        vol_mult = round(df['Volume'].iloc[-1] / df['Volume'].mean(), 1)
        ema = df['Close'].ewm(span=9).mean().iloc[-1]
        
        # Strength Score
        score = int(min(100, max(5, (50 + (((price - ema)/ema)*1800) + (vol_mult*10)))))
        color = "#FFD700" if score >= 85 else "#00ff00" if score >= 60 else "#ff3333"
        bar_html = f'<div class="bar-bg"><div class="bar-fill" style="width: {score}%; background: {color};"></div></div>'
        
        # Sector & News
        info = t.info
        sector = info.get('sector', 'Small Cap')
        
        cats = []
        if t.news:
            for n in t.news[:1]:
                title = n['title'].upper()
                label, css = ("BULLISH", "bullish") if any(x in title for x in ["FDA", "BEAT", "BUY", "SQUEEZE"]) else ("NEWS", "")
                cats.append({'t': ticker, 'title': n['title'], 'label': label, 'css': css})
                
        return {"ticker": ticker, "price": f"${price:.2f}", "vol": f"{vol_mult}x", "sector": sector, "bar": bar_html, "score": score, "cats": cats}
    except: return None

# --- 3. THE RENDER ---
scan_list = ["AEMD", "TPET", "MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "WULF", "SERV", "LUNR", "OKLO", "NNE", "SISI", "ZAPP", "KULR", "FFIE", "GWAV", "WKHS"]

results = []
for ticker in scan_list:
    d = get_data(ticker)
    if d: results.append(d)

# Top 20 Sort
top_20 = sorted(results, key=lambda x: x['score'], reverse=True)[:20]

# UI: SCANNER GRID
st.markdown('<div class="oracle-grid header-row"><div>Ticker</div><div>Price</div><div>Vol X</div><div>Sector</div><div>Strength</div><div>Signal</div></div>', unsafe_allow_html=True)
all_cats = []

if not top_20:
    st.warning("No tickers currently meeting $2-$20 criteria. Scanning for volatility...")
else:
    for d in top_20:
        sig = "🔥 GOLD" if d['score'] >= 85 else "⚡ ACTIVE"
        st.markdown(f"""
            <div class="oracle-grid data-row">
                <div style="color:#00ffcc;">{d['ticker']}</div>
                <div>{d['price']}</div>
                <div style="color:{'#00ff00' if float(d['vol'][:-1]) > 1.2 else '#666'};">{d['vol']}</div>
                <div style="font-size:12px; color:#aaa;">{d['sector']}</div>
                <div>{d['bar']}</div>
                <div style="font-size:12px; color:{'#FFD700' if 'GOLD' in sig else '#444'};">{sig}</div>
            </div>
            """, unsafe_allow_html=True)
        all_cats.extend(d['cats'])

# UI: CATALYST FEED
st.markdown('<br><h3>📰 LIVE CATALYST & SENTIMENT</h3>', unsafe_allow_html=True)
if all_cats:
    for c in all_cats:
        tag = f'<span class="tag {c["css"]}">{c["label"]}</span>' if c['css'] else ""
        st.markdown(f'<div class="catalyst-card">{tag} <b>{c["t"]}</b>: {c["title"]}</div>', unsafe_allow_html=True)
else:
    st.info("Waiting for fresh catalysts on the Top 20 list...")
