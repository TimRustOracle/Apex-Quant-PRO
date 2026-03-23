import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- 1. TERMINAL CONFIG ---
st.set_page_config(layout="wide", page_title="APEX PRO COMMAND")
st_autorefresh(interval=30000, key="terminal_heartbeat")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #050505; border-right: 1px solid #1a1a1a; min-width: 350px !important; }
    .stMetric { background: #0a0a0a; border: 1px solid #1a1a1a; padding: 10px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR CONTROLS (The "Settings" Panel) ---
with st.sidebar:
    st.title("⚙️ TERMINAL SETTINGS")
    
    st.subheader("Timeframe")
    tf_choice = st.selectbox("Select Interval", ["1m", "5m", "15m", "30m", "1h", "1d"], index=0)
    
    st.subheader("Indicators")
    ema_fast = st.number_input("Fast EMA Period", value=9, min_value=1)
    ema_slow = st.number_input("Slow EMA Period", value=21, min_value=1)
    show_volume = st.checkbox("Show Volume Panel", value=True)
    
    st.divider()
    st.subheader("Watchlist")
    # You can add/remove tickers here directly in the UI
    tickers = st.text_input("Assets (comma separated)", "MARA,SOUN,BBAI,PLTR,RIOT,LCID,NIO,GNS,HOLO,UPST,TPST").split(',')
    target = st.selectbox("FOCUS TICKER", [t.strip() for t in tickers])

# --- 3. THE ENGINE ---
@st.cache_data(ttl=25)
def get_live_data(symbol, interval):
    # Adjusting lookback period based on timeframe to keep the chart clean
    period = "1d" if "m" in interval else "1mo"
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    return df.dropna()

# --- 4. COMMAND DECK ---
if target:
    hist = get_live_data(target, tf_choice)
    
    if not hist.empty:
        # Calculate Dynamic Indicators
        hist['EMA_Fast'] = hist['Close'].ewm(span=ema_fast).mean()
        hist['EMA_Slow'] = hist['Close'].ewm(span=ema_slow).mean()
        
        # Header Metrics
        c1, c2, c3 = st.columns(3)
        curr_price = hist['Close'].iloc[-1]
        chg = ((curr_price - hist['Open'].iloc[0]) / hist['Open'].iloc[0]) * 100
        
        c1.metric(f"{target} PRICE", f"${curr_price:.2f}", f"{chg:.2f}%")
        c2.metric("INTERVAL", tf_choice)
        c3.metric("RVOL", f"{float(hist['Volume'].iloc[-1] / hist['Volume'].mean()):.1f}x")

        # MAIN CHARTING PANEL
        fig = go.Figure()

        # Add Candlesticks
        fig.add_trace(go.Candlestick(
            x=hist.index, open=hist['Open'], high=hist['High'],
            low=hist['Low'], close=hist['Close'], name="Price"
        ))

        # Add Dynamic EMAs
        fig.add_trace(go.Scatter(x=hist.index, y=hist['EMA_Fast'], line=dict(color='#00e5ff', width=1), name=f"EMA {ema_fast}"))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['EMA_Slow'], line=dict(color='#ff00ff', width=1), name=f"EMA {ema_slow}"))

        fig.update_layout(
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=600,
            paper_bgcolor="#000000",
            plot_bgcolor="#000000",
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)

        if show_volume:
            st.bar_chart(hist['Volume'].tail(50), color="#333333")

        # BOTTOM DATA GRID
        with st.expander("VIEW RAW TAPE DATA"):
            st.dataframe(hist.tail(20).sort_index(ascending=False), use_container_width=True)
else:
    st.info("Configure your watchlist in the sidebar to begin.")
