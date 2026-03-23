import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG ---
st.set_page_config(layout="wide", page_title="APEX ORACLE")
st_autorefresh(interval=30000, key="oracle_pulse")

# Custom "Vibrant Terminal" CSS
st.markdown("""
    <style>
    .stApp { background-color: #000; color: #00ffcc; font-family: 'Courier New', monospace; }
    .stTable { border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE ---
def get_oracle_data(ticker):
    try:
        # Fetching 5m data for velocity check
        df = yf.download(ticker, period="1d", interval="5m", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        price = df['Close'].iloc[-1]
        ema = df['Close'].ewm(span=9).mean().iloc[-1]
        
        # Volume Velocity (Current vol vs average 5m vol)
        current_vol = df['Volume'].iloc[-1]
        avg_vol = df['Volume'].mean()
        velocity = (current_vol / avg_vol) * 100
        
        # Strength Logic
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = 100 - (100 / (1 + (gain / loss)))
        
        # Clean Score (0-100)
        score = (rsi * 0.6) + (((price - ema) / ema) * 1000)
        score = round(min(100, max(0, score)), 0)
        
        return {
            "TICKER": ticker,
            "PRICE": f"${price:.2f}",
            "STRENGTH": int(score),
            "VELOCITY %": f"{int(velocity)}%",
            "SIGNAL": "🔥 BUY" if price > ema and rsi > 55 else "---",
            "RSI": int(rsi)
        }
    except: return None

# --- 3. THE DASHBOARD ---
st.title("🔮 APEX ORACLE COMMANDER")

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📡 MOMENTUM HEAT MAP")
    watchlist = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST"]
    
    data_list = [get_oracle_data(t) for t in watchlist if get_oracle_data(t) is not None]
    df = pd.DataFrame(data_list)

    if not df.empty:
        # HEAT MAP COLORING Logic
        def apply_heat(val):
            if val > 70: color = '#00ff00' # Bright Green
            elif val > 50: color = '#ffaa00' # Orange
            else: color = '#ff0000' # Red
            return f'background-color: {color}; color: black; font-weight: bold;'
        
        # Apply style and display as a clean table
        st.table(df.style.applymap(apply_heat, subset=['STRENGTH']))

with col2:
    st.subheader("📰 CATALYST FEED")
    st.success("STRENGTH: Look for Green (70+) for Apex setups.")
    st.info("VELOCITY: Values over 200% indicate heavy 'Tape' action.")
    st.divider()
    st.write("🛠 **Strategy:** Identify the Green Strength leaders, check for Velocity spikes, then flip to TradingView to execute.")
