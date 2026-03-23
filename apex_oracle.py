import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & ULTRA-SLIM STYLING ---
st.set_page_config(layout="wide", page_title="APEX ORACLE")
st_autorefresh(interval=30000, key="oracle_pulse")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #fff; }
    /* Compact Table Styling */
    table { width: 100%; border-collapse: collapse; color: white !important; }
    th { color: #00ffcc !important; text-align: left; padding: 4px !important; font-size: 14px; border-bottom: 1px solid #333; }
    td { padding: 4px !important; font-size: 16px !important; font-weight: bold; border-bottom: 1px solid #222; }
    /* Sliding Bar Styling */
    .bar-bg { background: #222; border-radius: 4px; width: 120px; height: 12px; display: inline-block; vertical-align: middle; }
    .bar-fill { height: 12px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE ---
def get_oracle_data(ticker):
    try:
        df = yf.download(ticker, period="1d", interval="5m", progress=False)
        if df is None or df.empty or len(df) < 15: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        price = float(df['Close'].iloc[-1])
        ema = df['Close'].ewm(span=9).mean().iloc[-1]
        
        # Simple RSI math
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = 100 - (100 / (1 + (gain / loss))) if loss != 0 else 50
        
        # Strength Score
        score = int(round((rsi * 0.6) + (((price - ema) / ema) * 1000), 0))
        score = min(100, max(0, score))
        
        # Color Transition: Red (0-59) -> Green (60-84) -> Gold (85-100)
        color = "#FFD700" if score >= 85 else "#00FF00" if score >= 60 else "#FF3333"

        bar_html = f'<div class="bar-bg"><div class="bar-fill" style="width: {score}%; background: {color};"></div></div>'

        return {
            "TICKER": ticker,
            "PRICE": f"${price:.2f}",
            "STRENGTH": bar_html,
            "SCORE": score,
            "SIGNAL": "🔥 BUY" if score >= 60 else "---"
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
    # Rendering only the columns we need for a smaller footprint
    display_cols = ["TICKER", "PRICE", "STRENGTH", "SIGNAL"]
    st.write(df[display_cols].to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.warning("Awaiting market data connection...")

st.caption("GOLD (85+) | GREEN (60+) | RED (0-59)")
