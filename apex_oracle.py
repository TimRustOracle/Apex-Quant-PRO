\import streamlit as st
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

# Custom Dark Theme
st.markdown("<style>.stApp { background-color: #000000; color: #ffffff; }</style>", unsafe_allow_html=True)

# --- 3. TAB NAVIGATION ---
tab1, tab2 = st.tabs(["📡 POWER RADAR (SCANNER)", "📊 COMMAND DECK (CHART)"])

# --- 4. DATA ENGINE ---
@st.cache_data(ttl=25)
def get_pro_data(symbol, interval):
    lookback = "1d" if "m" in interval else "2mo"
    return yf.download(symbol, period=lookback, interval=interval, progress=False).dropna()

# --- TAB 1: POWER RADAR ---
with tab1:
    st.header("POWER RADAR: MOMENTUM SCANNER")
    watchlist = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST"]
    
    scan_results = []
    for t in watchlist:
        try:
            d = yf.download(t, period="1d", interval="5m", progress=False).tail(5)
            if not d.empty:
                price = d['Close'].iloc[-1]
                chg = ((price - d['Open'].iloc[0]) / d['Open'].iloc[0]) * 100
                vol = d['Volume'].sum()
                scan_results.append({"SYMBOL": t, "PRICE": f"${price:.2f}", "CHANGE %": f"{chg:.2f}%", "VOL": vol})
        except: continue
    
    st.table(pd.DataFrame(scan_results)) # Clean, high-density grid

# --- TAB 2: COMMAND DECK ---
with tab2:
    if not PLOTLY_READY:
        st.error("🚨 PLOTLY ENGINE MISSING: Add 'plotly' to your requirements.txt file to unlock charts.")
    else:
        # Layout: Sidebar Controls + Main Chart
        with st.sidebar:
            st.title("⚙️ COMMANDER")
            target = st.selectbox("ENGAGE TICKER", watchlist)
            tf = st.selectbox("TIMEFRAME", ["1m", "5m", "15m", "1h", "1d"], index=0)
            ema_val = st.number_input("EMA PERIOD", value=9, min_value=1)
            rsi_val = st.slider("RSI PERIOD", 2, 30, 14)

        hist = get_pro_data(target, tf)
        if not hist.empty:
            # Indicator Logic
            hist['EMA'] = hist['Close'].ewm(span=ema_val).mean()
            
            # Create Pro Multi-Panel Chart
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.03, row_heights=[0.7, 0.3])

            # Row 1: Candlesticks & EMA Cloud
            fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'],
                                        low=hist['Low'], close=hist['Close'], name="Price"), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=hist['EMA'], line=dict(color='#00e5ff', width=1.5), name="EMA"), row=1, col=1)

            # Row 2: RSI
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_val).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_val).mean()
            rs = gain / loss
            hist['RSI'] = 100 - (100 / (1 + rs))
            
            fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], line=dict(color='#ffea00'), name="RSI"), row=2, col=1)
            fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

            fig.update_layout(template="plotly_dark", height=800, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
