import streamlit as st
import requests
import pandas as pd
import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. CORE CONFIG & KEYS ---
st.set_page_config(layout="wide", page_title="APEX COMMAND CENTER")
st_autorefresh(interval=60000, key="oracle_pulse")

AV_KEY = "VNHELWLTQGHT0IYT" 
FINNHUB_KEY = "d70n0i9r01ql6rnvssl0d70n0i9r01ql6rnvsslg"

current_time = datetime.datetime.now().strftime("%H:%M:%S")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #000; color: #fff; font-family: 'Arial', sans-serif; }}
    .top-bar {{ display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 2px solid #00ffcc; margin-bottom: 10px; }}
    .live-clock {{ font-size: 22px; font-weight: 900; color: #00ffcc; }}
    .oracle-grid {{ display: grid; grid-template-columns: 100px 100px 100px 120px 1fr 100px; gap: 15px; align-items: center; padding: 10px; border-bottom: 1px solid #222; }}
    .header-row {{ background-color: #111; color: #00ffcc !important; font-weight: bold; font-size: 13px; text-transform: uppercase; border-bottom: 2px solid #333; }}
    .data-row {{ font-size: 18px !important; font-weight: 900 !important; }}
    .bar-bg {{ background: #1a1a1a; border-radius: 4px; width: 100%; height: 16px; border: 1px solid #333; }}
    .bar-fill {{ height: 16px; border-radius: 3px; transition: width 0.8s ease-in-out; }}
    .sentiment-tag {{ padding: 2px 6px; border-radius: 3px; font-size: 11px; font-weight: bold; }}
    .bullish {{ background: #004d00; color: #00ff00; }}
    .bearish {{ background: #4d0000; color: #ff3333; }}
    .neutral {{ background: #333; color: #aaa; }}
    </style>
    <div class="top-bar">
        <div style="font-size: 24px; font-weight: 900;">🔮 APEX ORACLE: PRO EDITION</div>
        <div class="live-clock">🕒 {current_time}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 2. THE API ENGINES ---
def get_av_data(ticker):
    try:
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={AV_KEY}'
        data = requests.get(url).json().get('Global Quote', {})
        if not data: return None
        
        price = float(data.get('05. price', 0))
        # Keep your $2 - $20 strategy focus
        if not (2.0 <= price <= 25.0): return None
        
        change_pct = data.get('10. change percent', '0%')
        score = int(min(100, max(10, 50 + float(change_pct.strip('%')) * 4)))
        color = "#FFD700" if score >= 80 else "#00ff00" if score >= 50 else "#ff3333"
        bar_html = f'<div class="bar-bg"><div class="bar-fill" style="width: {score}%; background: {color};"></div></div>'
        
        return {"ticker": ticker, "price": f"${price:.2f}", "change": change_pct, "bar": bar_html, "score": score}
    except: return None

def get_pro_sentiment(ticker):
    try:
        # Pulls actual News Sentiment from Finnhub
        url = f'https://finnhub.io/api/v1/news-sentiment?symbol={ticker}&token={FINNHUB_KEY}'
        res = requests.get(url).json()
        buzz = res.get('buzz', {}).get('articlesInLastWeek', 0)
        s_score = res.get('sentiment', {}).get('bullishPercent', 0)
        
        if s_score > 0.6: return "BULLISH", "bullish"
        if s_score < 0.4 and s_score > 0: return "BEARISH", "bearish"
        return "NEUTRAL", "neutral"
    except: return "WAITING", "neutral"

def get_latest_news(ticker):
    try:
        url = f'https://finnhub.io/api/v1/company-news?symbol={ticker}&from=2026-03-01&to=2026-03-23&token={FINNHUB_KEY}'
        res = requests.get(url).json()
        if res: return res[0].get('headline', '')
        return ""
    except: return ""

# --- 3. RENDER SCANNER ---
# Focusing on your preferred high-momentum tickers
watchlist = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "WULF", "AEMD", "TPET", "SERV", "GWAV", "HOLO", "BTBT"]

results = []
# We scan top 5 to respect Alpha Vantage free tier limits per minute
for ticker in watchlist[:8]: 
    d = get_av_data(ticker)
    if d:
        label, css = get_pro_sentiment(ticker)
        d['sent_label'] = label
        d['sent_css'] = css
        d['news'] = get_latest_news(ticker)
        results.append(d)

# UI GRID
st.markdown('<div class="oracle-grid header-row"><div>Ticker</div><div>Price</div><div>Change %</div><div>Sentiment</div><div>Strength</div><div>Signal</div></div>', unsafe_allow_html=True)

if not results:
    st.warning("Scanning market for active $2-$25 runners...")
else:
    for d in sorted(results, key=lambda x: x['score'], reverse=True):
        sig = "🔥 GOLD" if d['score'] >= 80 else "⚡ ACTIVE"
        st.markdown(f"""
            <div class="oracle-grid data-row">
                <div style="color:#00ffcc;">{d['ticker']}</div>
                <div>{d['price']}</div>
                <div style="color:{'#00ff00' if '-' not in d['change'] else '#ff3333'};">{d['change']}</div>
                <div><span class="sentiment-tag {d['sent_css']}">{d['sent_label']}</span></div>
                <div>{d['bar']}</div>
                <div style="font-size:12px; color:{'#FFD700' if 'GOLD' in sig else '#444'};">{sig}</div>
            </div>
            """, unsafe_allow_html=True)

# --- 4. THE LIVE CATALYST FEED ---
st.markdown("<br><h3>📰 PRO CATALYST FEED (API DIRECT)</h3>", unsafe_allow_html=True)
for d in results:
    if d['news']:
        st.markdown(f"""
            <div style="background:#0a0a0a; padding:12px; border-left:4px solid #00ffcc; margin-bottom:8px; border-radius:0 4px 4px 0;">
                <b style="color:#00ffcc;">{d['ticker']}</b> | <span class="sentiment-tag {d['sent_css']}">{d['sent_label']}</span><br>
                <span style="font-size:14px;">{d['news']}</span>
            </div>
            """, unsafe_allow_html=True)
