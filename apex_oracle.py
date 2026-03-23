import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & HIGH-VIS STYLING ---
st.set_page_config(layout="wide", page_title="APEX ORACLE")
st_autorefresh(interval=30000, key="oracle_pulse")

# Force High Contrast & Large Text
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    h1, h2, h3 { color: #00FFCC !important; font-family: 'Arial Black'; }
    /* Make Table Text Bold and Large */
    .stTable td, .stTable th { 
        font-size: 20px !important; 
        font-weight: bold !important; 
        color: #FFFFFF !important;
        border: 1px solid #444 !important;
    }
    .metric-label { font-size: 18px !important; color: #00FFCC !important; }
    .metric-value { font-size: 32px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE ---
def get_oracle_data(ticker):
    try:
        df = yf.download(ticker, period="1d", interval="5m", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        price = df['Close'].iloc[-1]
        ema = df['Close'].ewm(span=9).mean().iloc[-1]
        
        # Volume Velocity
        velocity = (df['Volume'].iloc[-1] / df['Volume'].mean()) * 100
        
        # RSI Strength
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = 100 - (100 / (1 + (gain / loss)))
        
        # Clean Score (0-100)
        score = (rsi * 0.6) + (((price - ema) / ema) * 1000)
        score = int(round(min(100, max(0, score)), 0))
        
        return {
            "TICKER": ticker,
            "PRICE": f"${price:.2f}",
            "STRENGTH": score,
            "VOL %": f"{int(velocity)}%",
            "SIGNAL": "🔥 BUY" if price > ema and rsi > 55 else "---"
        }
    except: return None

# --- 3. THE DASHBOARD ---
st.title("🔮 APEX ORACLE: COMMANDER")

# TOP ROW: Overall Market Pulse
m1, m2, m3 = st.columns(3)
m1.metric("MARKET STATUS", "LIVE", delta="SCANNING", delta_color="normal")
m2.metric("REFRESH RATE", "30 SEC", "⚡ ACTIVE")
m3.metric("WATCHLIST COUNT", "11 TICKERS", "🛡️ APEX")

st.divider()

# MAIN ROW: Heat Map
watchlist = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST"]
data_list = [get_oracle_data(t) for t in watchlist if get_oracle_data(t) is not None]
df = pd.DataFrame(data_list)

if not df.empty:
    # High-Contrast Heat Map Logic
    def apply_heat(val):
        if val >= 70: color = '#00FF00' # Neon Green
        elif val >= 50: color = '#FFA500' # Bright Orange
        else: color = '#FF0000' # Bright Red
        return f'background-color: {color}; color: black; font-size: 24px; text-align: center;'

    st.table(df.style.applymap(apply_heat, subset=['STRENGTH']))

st.subheader("📰 STRATEGY NOTES")
st.info("Focus ONLY on GREEN 'STRENGTH' rows with 'VOL %' above 150%.")
