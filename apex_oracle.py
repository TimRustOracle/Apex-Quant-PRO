import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. ENGINE CONFIG ---
st.set_page_config(layout="wide", page_title="APEX PRO COMMAND")
st_autorefresh(interval=30000, key="terminal_heartbeat")

# --- 2. SIDEBAR: LIVE ADJUSTMENTS ---
with st.sidebar:
    st.title("⚙️ ENGINE SETTINGS")
    
    # ADJUST TIMEFRRAME (1m, 5m, 15m, etc.)
    tf_choice = st.selectbox("Select Interval", ["1m", "5m", "15m", "1h", "1d"], index=0)
    
    # ADJUST INDICATORS
    ema_val = st.number_input("EMA Cloud Period", value=9, min_value=1)
    
    st.divider()
    tickers = st.text_input("Watchlist", "MARA,SOUN,BBAI,PLTR,RIOT,LCID,NIO").split(',')
    target = st.selectbox("ENGAGE TERMINAL", [t.strip() for t in tickers])

# --- 3. DATA & CHARTING ---
if target:
    # Set lookback based on timeframe
    lookback = "1d" if "m" in tf_choice else "1mo"
    hist = yf.download(target, period=lookback, interval=tf_choice, progress=False).dropna()
    
    if not hist.empty:
        # Calculate Dynamic Indicator
        hist['EMA'] = hist['Close'].ewm(span=ema_val).mean()
        
        # PRO CANDLESTICK CHART
        fig = go.Figure(data=[
            go.Candlestick(
                x=hist.index, open=hist['Open'], high=hist['High'],
                low=hist['Low'], close=hist['Close'], name="Price"
            ),
            go.Scatter(x=hist.index, y=hist['EMA'], line=dict(color='#00e5ff', width=1), name=f"EMA {ema_val}")
        ])
        
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # RAW DATA TABLE
        st.dataframe(hist.tail(10).sort_index(ascending=False), use_container_width=True)
