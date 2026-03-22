import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. PRO UI CONFIG ---
st.set_page_config(layout="wide", page_title="Apex Quant AI", page_icon="🛡️")
st_autorefresh(interval=60 * 1000, key="quant_heartbeat")

st.markdown("""
    <style>
    .stApp { background-color: #05070a; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENHANCED DATA ENGINE ---
@st.cache_data(ttl=60)
def fetch_data(symbol):
    try:
        # Try 1-minute data first (Live Market)
        df = yf.download(symbol, period="2d", interval="1m", progress=False)
        
        # Weekend/After-Hours Fallback: Use Daily data if 1m is empty
        if df.empty or len(df) < 5:
            df = yf.download(symbol, period="60d", interval="1d", progress=False)
            is_live = False
        else:
            is_live = True

        if df.empty: return None
        
        # Fix Multi-index and Column Naming
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).lower() for c in df.columns]
        
        # Quant Indicators
        df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        
        return df, df.iloc[-1]['close'], is_live
    except Exception as e:
        return None

# --- 3. MAIN TERMINAL ---
st.title("🛡️ Apex Quant AI: Cloud Command")

with st.sidebar:
    st.header("Terminal Config")
    ticker = st.text_input("Enter Ticker", value="SOUN").upper()
    st.info("AI detects market status automatically.")

with st.status(f"Scanning {ticker} Matrix...", expanded=False) as status:
    bundle = fetch_data(ticker)
    if bundle:
        data, price, live_status = bundle
        mode_text = "LIVE 1M" if live_status else "DAILY (Market Closed)"
        status.update(label=f"Handshake Successful | Mode: {mode_text}", state="complete")
        
        # Header Stats
        c1, c2, c3 = st.columns(3)
        c1.metric("Last Price", f"${price:.2f}")
        c2.metric("Trend Info", "EMA 9 Cross" if price > data['ema9'].iloc[-1] else "Neutral")
        c3.metric("Data Mode", mode_text)
        
        # The Master Suite Chart
        fig = go.Figure(data=[go.Candlestick(
            x=data.index, open=data['open'], high=data['high'], low=data['low'], close=data['close'],
            name="Price"
        )])
        
        # Add Quantitative Overlays
        fig.add_trace(go.Scatter(x=data.index, y=data['vwap'], name="VWAP", line=dict(color='yellow', width=2)))
        fig.add_trace(go.Scatter(x=data.index, y=data['ema9'], name="EMA 9", line=dict(color='#3fb950', width=1.5)))
        
        fig.update_layout(
            height=750, 
            template="plotly_dark", 
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="#05070a",
            plot_bgcolor="#05070a"
        )
        fig.update_yaxes(side="right", gridcolor="#30363d")
        fig.update_xaxes(gridcolor="#30363d")
        
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
    else:
        status.update(label="Critical Error: Ticker Not Found", state="error")
        st.error(f"The AI could not find data for {ticker}. Please check the symbol.")
