import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & PRO-TRADER UI ---
st.set_page_config(layout="wide", page_title="APEX ORACLE")
st_autorefresh(interval=30000, key="oracle_pulse")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #fff; font-family: 'Arial', sans-serif; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th { color: #00ffcc !important; text-align: left; padding: 10px; font-size: 16px; border-bottom: 2px solid #333; }
    td { padding: 12px 10px !important; font-size: 20px !important; font-weight: 900 !important; border-bottom: 1px solid #222; }
    
    /* Dynamic Bar Styling */
    .bar-bg { background: #1a1a1a; border-radius: 6px; width: 150px; height: 16px; border: 1px solid #333; }
    .bar-fill { height: 16px; border-radius: 5px; transition: width 0.8s ease-in-out; }
    
    /* Ticker Link Styling */
    .ticker-link { color: #00ffcc; text-decoration: none; border-bottom: 1px dashed #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE ---
def get_oracle_data(ticker):
    try:
        df = yf.download(ticker, period="1d", interval="5m", progress=False)
        if df is None or df.empty or len(df) < 10: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        price = float(df['Close'].iloc[-1])
        ema = df['Close'].ewm(span=9).mean().iloc[-1]
        
        # Strength Logic
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = 100 - (100 / (1 + (gain / loss))) if loss != 0 else 50
        
        # Apex Score 0-100
        score = int(round((rsi * 0.5) + (((price - ema) / ema) * 1500), 0))
        score = min(100, max(5, score)) # Keep a tiny bit of bar visible
        
        # Color Thresholds: Red -> Green -> Gold
        if score >= 80: color = "linear-gradient(90deg, #FFD700, #FFA500)" # GOLD
        elif score >= 55: color = "#00ff00" # GREEN
        else: color = "#ff3333" # RED

        bar_html = f'<div class="bar-bg"><div class="bar-fill" style="width: {score}%; background: {color};"></div></div>'
        
        # TradingView Link
        tv_link = f'<a href="https://www.tradingview.com/chart/?symbol={ticker}" target="_blank" class="ticker-link">{ticker}</a>'

        return {
            "TICKER": tv_link,
            "PRICE": f"${price:.2f}",
            "STRENGTH": bar_html,
            "SIGNAL": "🔥 ENTRY" if score >= 60 else "---"
        }
    except: return None

# --- 3. THE DASHBOARD ---
st.title("🔮 APEX ORACLE")

watchlist = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST"]
data_list = []

for t in watchlist:
    res = get_oracle_data(t)
    if res: data_list.append(res)

if data_list:
    df = pd.DataFrame(data_list)
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.warning("📡 Connecting to Market Feed...")

st.markdown("---")
st.caption("🚀 **GOLD (80+)**: Extreme Breakout | **GREEN (55+)**: Trend Confirmed | **RED**: Neutral/Weak")
