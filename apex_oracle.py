import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. PRO UI CONFIG ---
st.set_page_config(layout="wide", page_title="Apex Quant AI")
st_autorefresh(interval=60 * 1000, key="quant_heartbeat")

st.markdown("""
    <style>
    .stApp { background-color: #05070a; color: #ffffff; }
    .status-box { padding: 10px; border-radius: 5px; background: #1a1d23; border-left: 5px solid #58a6ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. QUANT ENGINE ---
@st.cache_data(ttl=30)
def fetch_data(symbol):
    try:
        df = yf.download(symbol, period="2d", interval="1m", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).lower() for c in df.columns]
        
        # Quant Indicators
        df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        return df, df.iloc[-1]['close']
    except:
        return None

# --- 3. MAIN TERMINAL ---
st.title("🛡️ Apex Quant AI: Cloud Command")

ticker = st.sidebar.text_input("Enter Ticker", value="SOUN").upper()

with st.status(f"AI Engine: Scanning {ticker}...", expanded=True) as status:
    bundle = fetch_data(ticker)
    if bundle:
        status.update(label="Connection Secured: Data Stream Active", state="complete")
        data, price = bundle
        
        st.subheader(f"{ticker} | Live Price: ${price:.2f}")
        
        # Pro Chart Restoration
        fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['open'], high=data['high'], low=data['low'], close=data['close'])])
        fig.add_trace(go.Scatter(x=data.index, y=data['vwap'], name="VWAP", line=dict(color='yellow', width=2)))
        fig.add_trace(go.Scatter(x=data.index, y=data['ema9'], name="EMA 9", line=dict(color='green', width=1.5)))
        
        fig.update_layout(height=700, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=0, r=40, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
    else:
        status.update(label="Awaiting Market Data...", state="error")
        st.warning("Ensure the market is open or check the ticker symbol.")
