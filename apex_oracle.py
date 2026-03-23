import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- 1. ENGINE CHECK ---
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_READY = True
except ImportError:
    PLOTLY_READY = False

# --- 2. CONFIG & REFRESH ---
st.set_page_config(layout="wide", page_title="APEX MASTER SUITE")
st_autorefresh(interval=30000, key="global_heartbeat")

# --- 3. TAB NAVIGATION ---
tab1, tab2 = st.tabs(["📡 POWER RADAR", "📊 COMMAND DECK"])

# --- 4. DATA ENGINE ---
@st.cache_data(ttl=25)
def get_data(symbol, interval):
    lookback = "1d" if "m" in interval else "1mo"
    return yf.download(symbol, period=lookback, interval=interval, progress=False).dropna()

# --- TAB 1: THE SCANNER (Full Screen Radar) ---
with tab1:
    st.header("POWER RADAR: MOMENTUM SCAN")
    watchlist = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST"]
    
    # Simple logic for the scanner table
    scan_data = []
    for t in watchlist:
        d = yf.download(t, period="1d", interval="5m", progress=False).tail(2)
        if not d.empty:
            price = d['Close'].iloc[-1]
            chg = ((price - d['Open'].iloc[0]) / d['Open'].iloc[0]) * 100
            scan_data.append({"SYMBOL": t, "PRICE": round(price, 2), "CHANGE %": round(chg, 2)})
    
    st.dataframe(pd.DataFrame(scan_data), use_container_width=True, height=600)

# --- TAB 2: THE CHART (Dedicated Trading View) ---
with tab2:
    if not PLOTLY_READY:
        st.error("🚨 CHART ENGINE MISSING: Please add 'plotly' to your requirements.txt file.")
    else:
        c1, c2 = st.columns([1, 4])
        with c1:
            target = st.selectbox("FOCUS TICKER", watchlist)
            tf = st.selectbox("TIMEFRAME", ["1m", "5m", "15m", "1h", "1d"])
            ema_val = st.number_input("EMA CLOUD", value=9)
            rsi_val = st.slider("RSI PERIOD", 2, 30, 14)

        with c2:
            hist = get_data(target, tf)
            if not hist.empty:
                # Calculations
                hist['EMA'] = hist['Close'].ewm(span=ema_val).mean()
                
                # Pro Multi-Panel Chart
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                   vertical_spacing=0.02, row_heights=[0.7, 0.3])
                
                fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'],
                                            low=hist['Low'], close=hist['Close'], name="Price"), row=1, col=1)
                fig.add_trace(go.Scatter(x=hist.index, y=hist['EMA'], line=dict(color='#00e5ff'), name="EMA"), row=1, col=1)
                
                fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
