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
    .top-bar {{ display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 2px solid #00ffcc; margin-bottom: 20px; }}
    .live-clock {{ font-size: 24px; font-weight: 900; color: #00ffcc; }}
    .oracle-grid {{ display: grid; grid-template-columns: 120px 100px 100px 1fr 120px; gap: 15px; align-items: center; padding: 10px; border-bottom: 1px solid #222; }}
    .header-row {{ background-color: #111; color: #00ffcc !important; font-weight: bold; font-size: 13px; text-transform: uppercase; border-bottom: 2px solid #333; position: sticky; top: 0; z-index: 99; }}
    .data-row {{ font-size: 20px !important; font-weight: 900 !important; }}
    .bar-bg {{ background: #1a1a1a; border-radius: 4px; width: 100%; height: 16px; border: 1px solid #333; }}
    .bar-fill {{ height: 16px; border-radius: 3px; transition: width 0.8s ease-in-out; }}
    
    /* Sentiment Feed Styling */
    .catalyst-card {{ background: #0a0a0a; padding: 15px; border-left: 5px solid #00ffcc; margin-bottom: 10px; border-radius: 0 5px 5px 0; border-top: 1px solid #222; }}
    .tag {{ padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; text-transform: uppercase; margin-right: 10px; }}
    .bullish {{ background: #004d00; color: #00ff00; }}
    .bearish {{ background: #4d0000; color: #ff3333; }}
    .alert {{ background: #4d3d00; color: #ffcc00; }}
    </style>
    <div class="top-bar">
        <div style="font-size: 28px; font-weight: 900;">🔮 APEX ORACLE: COMMAND CENTER</div>
        <div class="live-clock">🕒 {current_time}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 2. SENTIMENT & CATALYST ENGINE ---
def analyze_catalyst(title):
    title = title.upper()
    # High Conviction Day Trading Keywords
    bull_keywords = ["FDA", "APPROVAL", "EARNINGS BEAT", "PARTNERSHIP", "ACQUISITION", "CONTRACT", "SQUEEZE", "BREAKOUT", "UPGRADE"]
    bear_keywords = ["OFFERING", "DILUTION", "MISS", "DOWNGRADE", "LAWSUIT", "INVESTIGATION", "HALT"]
    
    if any(word in title for word in bull_keywords): return "BULLISH", "bullish"
    if any(word in title for word in bear_keywords): return "BEARISH", "bearish"
    return "CATALYST", "alert"

def get_oracle_data(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="3d", interval="5m")
        if df.empty: return None
        
        price = float(df['Close'].iloc[-1])
        if not (2.0 <= price <= 20.0): return None # Filter check

        # Volume & Momentum Math
        vol_mult = round(df['Volume'].iloc[-1] / df['Volume'].mean(), 1)
        ema = df['Close'].ewm(span=9).mean().iloc[-1]
        score = int(min(100, max(5, (50 + (((price - ema) / ema) * 2000) + (vol_mult * 5)))))
        
        color = "#FFD700" if score >= 85 else "#00ff00" if score >= 60 else "#ff3333"
        bar_html = f'<div class="bar-bg"><div class="bar-fill" style="width: {score}%; background: {color};"></div></div>'
        
        # Pulling news for catalysts
        ticker_catalysts = []
        if t.news:
            for n in t.news[:2]:
                label, css = analyze_catalyst(n['title'])
                ticker_catalysts.append({
                    'ticker': ticker,
                    'title': n['title'],
                    'label': label,
                    'css': css,
                    'link': n.get('link', '#')
                })

        return {"ticker": ticker, "price": f"${price:.2f}", "vol_mult": f"{vol_mult}x", "bar": bar_html, "score": score, "catalysts": ticker_catalysts}
    except: return None

# --- 3. DYNAMIC SCAN & RENDER ---
# Deep Pool Scan
deep_scan = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST", "TPET", "BTBT", "MSTR", "WULF", "AEMD", "SERV", "LUNR", "OKLO", "NNE", "SISI", "ZAPP", "AEI", "KULR", "TTOO", "FFIE", "GWAV", "PTON", "AADI", "LAES", "TCBP", "OCEA", "ADTX", "BNGO", "WKHS", "NKLA"]

all_results = [get_oracle_data(t) for t in deep_scan]
valid_results = [r for r in all_results if r]
top_20 = sorted(valid_results, key=lambda x: x['score'], reverse=True)[:20]

# Display Scanner Grid
st.markdown('<div class="oracle-grid header-row"><div>TICKER</div><div>PRICE</div><div>VOL X</div><div>STRENGTH</div><div>SIGNAL</div></div>', unsafe_allow_html=True)
global_catalysts = []

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
    global_catalysts.extend(d['catalysts'])

# Display Catalyst Feed
st.markdown("<br><br><h2>📰 LIVE CATALYST & SENTIMENT FEED</h2>", unsafe_allow_html=True)
if global_catalysts:
    for c in global_catalysts[:12]:
        st.markdown(f"""
            <div class="catalyst-card">
                <span class="tag {c['css']}">{c['label']}</span>
                <b style="color:#00ffcc;">{c['ticker']}</b>: {c['title']}
                <br><a href="{c['link']}" target="_blank" style="color:#555; font-size:12px;">Full Report →</a>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("Scanning for social sentiment and news catalysts...")
