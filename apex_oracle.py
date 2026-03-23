import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & GRID ALIGNMENT ---
st.set_page_config(layout="wide", page_title="APEX ORACLE")
st_autorefresh(interval=30000, key="oracle_pulse")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #fff; }
    .oracle-grid { display: grid; grid-template-columns: 1fr 1fr 2fr 1fr; gap: 10px; align-items: center; padding: 10px; border-bottom: 1px solid #222; }
    .header-row { background-color: #111; color: #00ffcc !important; font-weight: bold; font-size: 14px; text-transform: uppercase; border-bottom: 2px solid #333; }
    .data-row { font-size: 18px !important; font-weight: 900 !important; }
    .bar-bg { background: #1a1a1a; border-radius: 4px; width: 100%; height: 12px; border: 1px solid #333; }
    .bar-fill { height: 12px; border-radius: 3px; }
    .news-card { background: #0a0a0a; padding: 10px; border-left: 3px solid #00ffcc; margin-bottom: 5px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE (WITH FILTERS) ---
def get_oracle_data(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1d", interval="5m")
        if df.empty: return None
        
        price = float(df['Close'].iloc[-1])
        volume = t.info.get('regularMarketVolume', 0)
        
        # --- DAY TRADING FILTER ($2-$20 & High Volume) ---
        if not (2.0 <= price <= 20.0) or volume < 500000:
            return None

        ema = df['Close'].ewm(span=9).mean().iloc[-1]
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = 100 - (100 / (1 + (gain / loss))) if loss != 0 else 50
        
        score = int(round((rsi * 0.5) + (((price - ema) / ema) * 1500), 0))
        score = min(100, max(5, score))
        color = "#FFD700" if score >= 80 else "#00ff00" if score >= 55 else "#ff3333"
        bar_html = f'<div class="bar-bg"><div class="bar-fill" style="width: {score}%; background: {color};"></div></div>'
        
        return {"ticker": ticker, "price": f"${price:.2f}", "bar": bar_html, "news": t.news[:2]}
    except: return None

# --- 3. THE DASHBOARD ---
st.title("🔮 APEX ORACLE: COMMAND CENTER")
col_main, col_news = st.columns([2, 1])

watchlist = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST", "TPET", "BTBT"]

with col_main:
    st.subheader("📡 SCANNER (FILTERED: $2-$20)")
    st.markdown('<div class="oracle-grid header-row"><div>TICKER</div><div>PRICE</div><div>STRENGTH</div><div>STATUS</div></div>', unsafe_allow_html=True)
    
    active_news = []
    for t in watchlist:
        data = get_oracle_data(t)
        if data:
            st.markdown(f"""
                <div class="oracle-grid data-row">
                    <div><a href="https://www.tradingview.com/chart/?symbol={data['ticker']}" target="_blank" style="color:#00ffcc; text-decoration:none;">{data['ticker']}</a></div>
                    <div>{data['price']}</div>
                    <div>{data['bar']}</div>
                    <div style="font-size:12px; color:#aaa;">ACTIVE</div>
                </div>
                """, unsafe_allow_html=True)
            active_news.extend(data['news'])

with col_news:
    st.subheader("📰 CATALYST FEED")
    if not active_news:
        st.write("No major catalysts for filtered tickers.")
    for n in active_news:
        st.markdown(f"""
            <div class="news-card">
                <b>{n['publisher']}</b>: {n['title']}<br>
                <a href="{n['link']}" target="_blank" style="color:#555; font-size:12px;">Read More</a>
            </div>
            """, unsafe_allow_html=True)
