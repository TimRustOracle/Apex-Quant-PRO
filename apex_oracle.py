import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- 1. ENGINE SAFETY CHECK ---
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_READY = True
except ImportError:
    PLOTLY_READY = False

# --- 2. LAYOUT & REFRESH ---
st.set_page_config(layout="wide", page_title="APEX PRO COMMAND")
st_autorefresh(interval=30000, key="apex_heartbeat")

st.markdown("<style>.stApp { background-color: #000; color: #fff; }</style>", unsafe_allow_html=True)

# --- 3. SIDEBAR: THE COMMAND CENTER ---
with st.sidebar:
    st.title("⚙️ ENGINE SETTINGS")
    
    # LIVE TIMEFRAME SWITCHER
    tf = st.selectbox("Interval", ["1m", "5m", "15m", "1h", "1d"], index=0)
    
    # ADJUSTABLE INDICATORS
    ema_p = st.number_input("EMA Cloud", value=9, min_value=1)
    rsi_p = st.slider("RSI Period", 2, 30, 14)
    
    st.divider()
    tickers = st.text_input("Watchlist", "MARA,SOUN,BBAI,PLTR,RIOT,LCID,NIO")
    target = st.selectbox("ENGAGE TERMINAL", [t.strip() for t in tickers.split(',')])

# --- 4. THE VISUAL DECK ---
if not PLOTLY_READY:
    st.warning("⚠️ ENGINE PENDING: Add 'requirements.txt' to your repo to unlock Pro Charts.")
    st.stop()

if target:
    # Fetch Data based on Timeframe
    lookback = "1d" if "m" in tf else "1mo"
    df = yf.download(target, period=lookback, interval=tf, progress=False).dropna()
    
    if not df.empty:
        # Technicals
        df['EMA'] = df['Close'].ewm(span=ema_p).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_p).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_p).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))

        # PRO MULTI-PANEL DASHBOARD
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.03, row_heights=[0.7, 0.3])

        # Candlesticks
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name="Price"
        ), row=1, col=1)
        
        # EMA Cloud
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA'], line=dict(color='#00e5ff', width=1.5), name="EMA"), row=1, col=1)

        # RSI Panel
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#ffea00', width=1.2), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

        fig.update_layout(template="plotly_dark", height=750, xaxis_rangeslider_visible=False,
                          margin=dict(l=10, r=10, t=10, b=10))
        
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("RAW TAPE"):
            st.dataframe(df.tail(10).sort_index(ascending=False), use_container_width=True)
