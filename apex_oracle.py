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

# Bloomberg-Style Dark Theme
st.markdown("<style>.stApp { background-color: #000; color: #fff; }</style>", unsafe_allow_html=True)

# --- 3. TAB NAVIGATION ---
tab1, tab2, tab3 = st.tabs(["📡 POWER RADAR", "📊 COMMAND DECK", "🧠 STRATEGY ANALYZER"])

# --- 4. DATA ENGINE (FIXED FOR MULTI-INDEX) ---
def fetch_clean_data(symbol, interval):
    lookback = "1d" if "m" in interval else "2mo"
    df = yf.download(symbol, period=lookback, interval=interval, progress=False)
    
    if df.empty:
        return pd.DataFrame()
    
    # Fix for yfinance MultiIndex issue that causes ValueErrors
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    return df.dropna()

# --- TAB 1: POWER RADAR ---
with tab1:
    st.header("RADAR: LIVE MOMENTUM SCAN")
    watchlist = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST"]
    
    scan_results = []
    for t in watchlist:
        try:
            d = fetch_clean_data(t, "5m").tail(5)
            if not d.empty:
                price = float(d['Close'].iloc[-1])
                open_p = float(d['Open'].iloc[0])
                chg = ((price - open_p) / open_p) * 100
                scan_results.append({"SYMBOL": t, "PRICE": f"${price:.2f}", "CHANGE %": f"{chg:.2f}%"})
        except: continue
    st.table(pd.DataFrame(scan_results))

# --- TAB 2: COMMAND DECK ---
with tab2:
    if not PLOTLY_READY:
        st.error("🚨 PLOTLY MISSING: Add 'plotly' to your requirements.txt to unlock Pro Charts.")
    else:
        with st.sidebar:
            st.title("⚙️ COMMANDER")
            target = st.selectbox("ENGAGE TICKER", watchlist)
            tf = st.selectbox("TIMEFRAME", ["1m", "5m", "15m", "1h", "1d"], index=0)
            ema_p = st.number_input("EMA CLOUD", value=9, min_value=1)
            rsi_p = st.slider("RSI PERIOD", 2, 30, 14)

        hist = fetch_clean_data(target, tf)
        if not hist.empty:
            # Safe Indicator Calculation
            hist['EMA'] = hist['Close'].ewm(span=ema_p).mean()
            
            # RSI Logic
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_p).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_p).mean()
            hist['RSI'] = 100 - (100 / (1 + (gain / loss)))

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            # Price & EMA
            fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Price"), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=hist['EMA'], line=dict(color='#00e5ff', width=1.5), name="EMA"), row=1, col=1)
            
            # RSI
            fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], line=dict(color='#ffea00'), name="RSI"), row=2, col=1)
            fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

            fig.update_layout(template="plotly_dark", height=800, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: STRATEGY ANALYZER ---
with tab3:
    st.header("STRATEGY ANALYZER")
    st.info("Log your missed setups to track performance.")
    missed_ticker = st.text_input("Missed Ticker", "MARA")
    if st.button("LOG MISSED TRADE"):
        st.success(f"Logged {missed_ticker} for review.")
