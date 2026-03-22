import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- 1. CORE BRAIN & SYNC ---
st.set_page_config(layout="wide", page_title="Apex Strategic Command", page_icon="🛡️")
st_autorefresh(interval=60 * 1000, key="momentum_sync")

# Fix for "None" error: Ensure a ticker is ALWAYS selected
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "SOUN"

# Professional iMac Styling
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1d23; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; min-width: 300px; }
    .risk-card { background: #fffbe6; padding: 15px; border-radius: 10px; border: 1.5px solid #ffe58f; margin-bottom: 10px; }
    .signal-banner { padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; color: white; margin-bottom: 20px; }
    div.stButton > button { width: 100%; border-radius: 4px; height: 45px; font-weight: bold; font-size: 0.75rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. RESTORED DATA ENGINE ---
@st.cache_data(ttl=300)
def get_apex_intelligence(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty: return None
        
        # Restoration of EMA 9 & RVOL
        last = df.iloc[-1]
        ema9_series = df['Close'].ewm(span=9, adjust=False).mean()
        last_ema9 = ema9_series.iloc[-1]
        rvol = last['Volume'] / df['Volume'].mean()
        change = ((last['Close'] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
        
        # Bullish/Bearish Logic
        is_bullish = last['Close'] > last_ema9
        banner_color = "#28a745" if is_bullish else "#dc3545"
        banner_text = "STRATEGIC ALIGNMENT: BULLISH" if is_bullish else "STRATEGIC ALIGNMENT: BEARISH"
        
        return {
            "price": last['Close'], "ema9": last_ema9, "rvol": rvol, "change": change,
            "df": df, "ema_series": ema9_series, "color": banner_color, "text": banner_text
        }
    except: return None

# --- 3. WATCHLIST & SIDEBAR ---
watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
st.sidebar.header("⚡ Momentum Scan")
choice = st.sidebar.radio("Active Terminal", watchlist, index=watchlist.index(st.session_state.selected_ticker))

if choice != st.session_state.selected_ticker:
    st.session_state.selected_ticker = choice
    st.rerun()

# --- 4. MAIN COMMAND TERMINAL ---
intel = get_apex_intelligence(st.session_state.selected_ticker)

if intel:
    st.title(f"🛡️ {st.session_state.selected_ticker} Command")
    
    # Restored Signal Banner
    st.markdown(f'<div class="signal-banner" style="background-color:{intel["color"]};">⚠️ {intel["text"]}</div>', unsafe_allow_html=True)
    
    # Restored Metric Bar
    m1, m2, m3 = st.columns(3)
    m1.metric("Price", f"${intel['price']:.2f}")
    m2.metric("EMA 9", f"${intel['ema9']:.2f}", f"{(intel['price'] - intel['ema9']):+.2f}")
    m3.metric("RVOL", f"{intel['rvol']:.2f}x")

    # Technical Chart (Price + EMA 9)
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(intel['df'].index, intel['df']['Close'], color='#0066cc', label='Price', linewidth=2)
    ax.plot(intel['ema_series'].index, intel['ema_series'], color='#28a745', label='EMA 9', linestyle='--', alpha=0.8)
    ax.set_facecolor('white'); fig.patch.set_facecolor('white')
    ax.legend(prop={'size': 8})
    st.pyplot(fig)

    # RISK SHIELD CALCULATOR
    st.divider()
    entry = intel['price']
    stop = entry * 0.98 # 2% Stop Loss rule
    shares = 100 / (entry - stop) # $100 Fixed Risk
    
    st.markdown(f"""
        <div class="risk-card">
            <span style="font-weight:bold; color:#856404;">🛡️ RISK SHIELD (Fixed $100 Risk)</span><br>
            <b>Target Buy:</b> {int(shares)} Shares | <b>Stop Loss:</b> ${stop:.2f} | <b>Total Position:</b> ${(shares * entry):.2f}
        </div>
    """, unsafe_allow_html=True)
    
    # Integrated Heat Map
    st.caption("Quick Sync Heat Map")
    h_cols = st.columns(len(watchlist))
    for i, ticker in enumerate(watchlist):
        if h_cols[i].button(ticker, key=f"btn_{ticker}"):
            st.session_state.selected_ticker = ticker
            st.rerun()
