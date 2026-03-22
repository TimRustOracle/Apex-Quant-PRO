import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- 1. SETTINGS & REFRESH ---
st.set_page_config(layout="wide", page_title="Apex Strategic Command")
st_autorefresh(interval=60 * 1000, key="momentum_sync")

# Force-initialize to prevent selection errors
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "SOUN"

# --- 2. DEFENSIVE DATA ENGINE ---
@st.cache_data(ttl=300)
def get_market_intelligence(ticker):
    try:
        # Standard 60d pull with a strict timeout
        df = yf.download(ticker, period="60d", interval="1d", progress=False, timeout=10)
        if df.empty or len(df) < 10: return None
        
        # Technical Calculations
        ema9_series = df['Close'].ewm(span=9, adjust=False).mean()
        price = df['Close'].iloc[-1]
        ema_val = ema9_series.iloc[-1]
        rvol = df['Volume'].iloc[-1] / df['Volume'].mean()
        
        # Signal Banner Logic
        is_bullish = price > ema_val
        color = "#28a745" if is_bullish else "#dc3545"
        text = "STRATEGIC ALIGNMENT: BULLISH" if is_bullish else "STRATEGIC ALIGNMENT: BEARISH"
        
        return {
            "df": df, "price": price, "ema9": ema_val, 
            "ema_series": ema9_series, "rvol": rvol, 
            "color": color, "text": text
        }
    except Exception:
        return None

# --- 3. SIDEBAR NAVIGATION ---
watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
st.sidebar.title("⚡ Momentum Scan")
choice = st.sidebar.selectbox("Active Terminal", watchlist, 
                              index=watchlist.index(st.session_state.selected_ticker))

if choice != st.session_state.selected_ticker:
    st.session_state.selected_ticker = choice
    st.rerun()

# --- 4. MAIN INTERFACE ---
intel = get_market_intelligence(st.session_state.selected_ticker)

if intel:
    st.title(f"🛡️ {st.session_state.selected_ticker} Command")
    
    # SIGNAL BANNER (Restored)
    st.markdown(f"""
        <div style="background-color:{intel['color']}; padding:15px; border-radius:5px; text-align:center; color:white; font-weight:bold;">
            ⚠️ {intel['text']}
        </div>
    """, unsafe_allow_html=True)
    
    # METRICS ROW (Restored)
    m1, m2, m3 = st.columns(3)
    m1.metric("Current Price", f"${intel['price']:.2f}")
    m2.metric("EMA 9 (Trend)", f"${intel['ema9']:.2f}", f"{(intel['price'] - intel['ema9']):+.2f}")
    m3.metric("RVOL", f"{intel['rvol']:.2f}x")

    # THE TECHNICAL CHART (Restored EMA 9)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(intel['df'].index, intel['df']['Close'], color='#0066cc', label='Price Action', linewidth=2)
    ax.plot(intel['ema_series'].index, intel['ema_series'], color='#28a745', label='EMA 9', linestyle='--', alpha=0.8)
    ax.set_facecolor('white')
    ax.legend()
    st.pyplot(fig)
    
    # RISK SHIELD (Simplified for Stability)
    st.divider()
    stop = intel['price'] * 0.98
    shares = 100 / (intel['price'] - stop)
    st.info(f"🛡️ RISK SHIELD: To risk exactly $100, buy {int(shares)} shares with a Stop Loss at ${stop:.2f}")

else:
    st.warning("🔄 System is synchronizing with market data. If this persists, please check your internet connection.")
    if st.button("Force Reconnect"):
        st.cache_data.clear()
        st.rerun()
