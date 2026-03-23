import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG ---
st.set_page_config(layout="wide", page_title="APEX ORACLE")
st_autorefresh(interval=30000, key="oracle_pulse") # Auto-refresh every 30s

# Vibrant Terminal Styling
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #00ffcc; }
    .stTable { background-color: #0a0a0a; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE SCANNER ENGINE ---
def get_oracle_data(ticker):
    try:
        df = yf.download(ticker, period="1d", interval="5m", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        price = df['Close'].iloc[-1]
        ema = df['Close'].ewm(span=9).mean().iloc[-1]
        
        # Strength Logic (RSI + Momentum)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = 100 - (100 / (1 + (gain / loss)))
        
        # Strength Score 0-100
        score = (rsi * 0.7) + (((price - ema) / ema) * 1000)
        score = round(min(100, max(0, score)), 1)
        
        return {
            "TICKER": ticker,
            "PRICE": f"${price:.2f}",
            "STRENGTH": score,
            "SIGNAL": "🔥 APEX BUY" if price > ema and rsi > 50 else "---",
            "RSI": round(rsi, 1)
        }
    except: return None

# --- 3. THE DASHBOARD ---
st.title("🔮 APEX ORACLE SCANNER")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📡 MOMENTUM HEAT MAP")
    watchlist = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST"]
    
    results = [get_oracle_data(t) for t in watchlist if get_oracle_data(t) is not None]
    df = pd.DataFrame(results)

    if not df.empty:
        # HEAT MAP COLORING
        def apply_heat(val):
            color = 'red' if val < 40 else 'orange' if val < 60 else 'green'
            return f'background-color: {color}; color: white; font-weight: bold'
        
        st.table(df.style.applymap(apply_heat, subset=['STRENGTH']))

with col2:
    st.subheader("📰 NEWS & SENTIMENT")
    st.info("MARA: BTC strength driving crypto proxies.")
    st.warning("SOUN: Eyeing resistance at $6.50.")
    st.success("BBAI: AI sector seeing fresh volume inflow.")
    
    st.divider()
    st.write("📈 **Instructions:** Find the 'Green' strength stocks here, then execute the setup on TradingView.")
