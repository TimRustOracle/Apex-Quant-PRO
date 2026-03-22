import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- 1. CORE STABILITY & REFRESH ---
st.set_page_config(layout="wide", page_title="Apex Command Safe Mode")
# Reduced refresh to 2 mins to give the iMac more breathing room
st_autorefresh(interval=120 * 1000, key="momentum_sync")

# Pre-set ticker to prevent the "None" selection crash
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "SOUN"

# Clean UI Styling for older hardware
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1d23; }
    .signal-banner { padding: 15px; border-radius: 5px; text-align: center; font-weight: bold; color: white; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE WITH TIMEOUT PROTECTION ---
@st.cache_data(ttl=300)
def get_stable_data(ticker):
    try:
        # Standard 60d pull
        df = yf.download(ticker, period="60d", interval="1d", progress=False, timeout=10)
        if df.empty: return None
        
        # Core Technicals
        ema9_series = df['Close'].ewm(span=9, adjust=False).mean()
        price = df['Close'].iloc[-1]
        ema_val = ema9_series.iloc[-1]
        rvol = df['Volume'].iloc[-1] / df['Volume'].mean()
        
        # Bullish/Bearish Signal
        is_bullish = price > ema_val
        color = "#28a745" if is_bullish else "#dc3545"
        text = "STRATEGIC ALIGNMENT: BULLISH" if is_bullish else "STRATEGIC ALIGNMENT: BEARISH"
        
        return {"df": df, "price": price, "ema9": ema_val, "ema_series": ema9_series, "rvol": rvol, "color": color, "text": text}
    except:
        return None

# --- 3. SIDEBAR NAVIGATION ---
watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
st.sidebar.title("⚡ Momentum Scan")
choice = st.sidebar.selectbox("Active Terminal", watchlist, index=watchlist.index(st.session_state.selected_ticker))

if choice != st.session_state.selected_ticker:
    st.session_state.selected_ticker = choice
    st.rerun()

# --- 4. MAIN INTERFACE ---
data = get_stable_data(st.session_state.selected_ticker)

if data:
    st.title(f"🛡️ {st.session_state.selected_ticker} Command")
    
    # Restored Logic Banner
    st.markdown(f'<div class="signal-banner" style="background-color:{data["color"]};">⚠️ {data["text"]}</div>', unsafe_allow_html=True)
    
    # Core Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Current Price", f"${data['price']:.2f}")
    m2.metric("EMA 9", f"${data['ema9']:.2f}")
    m3.metric("RVOL", f"{data['rvol']:.2f}x")

    # The Technical Chart (EMA 9 restoration)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(data['df'].index, data['df']['Close'], color='#0066cc', label='Price Action', linewidth=2)
    ax.plot(data['ema_series'].index, data['ema_series'], color='#28a745', label='EMA 9 (Trend)', linestyle='--', alpha=0.8)
    ax.set_facecolor('white')
    ax.legend(prop={'size': 9})
    st.pyplot(fig)
else:
    # This prevents the white screen by showing an error message instead
    st.warning("⚠️ Connection to Yahoo Finance timed out. Your iMac is catching its breath—please click the refresh button below.")
    if st.button("Refresh Terminal"):
        st.cache_data.clear()
        st.rerun()
