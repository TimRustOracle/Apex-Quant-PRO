import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- 1. CORE BRAIN & CRASH PROTECTION ---
st.set_page_config(layout="wide", page_title="Apex Command", page_icon="🛡️")
st_autorefresh(interval=60 * 1000, key="momentum_sync")

# Force-initialize the ticker to prevent "None" blank screens
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "SOUN"

# Clean UI Styling for iMac
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1d23; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; min-width: 300px; }
    .risk-card { background: #fffbe6; padding: 15px; border-radius: 10px; border: 1.5px solid #ffe58f; margin-top: 20px; }
    .signal-banner { padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; color: white; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE (NO CRASH LOGIC) ---
@st.cache_data(ttl=300)
def get_clean_data(ticker):
    try:
        # Standardize data pull
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty: return None
        
        # Calculate EMA 9 and RVOL
        ema9_series = df['Close'].ewm(span=9, adjust=False).mean()
        last_price = df['Close'].iloc[-1]
        last_ema9 = ema9_series.iloc[-1]
        rvol = df['Volume'].iloc[-1] / df['Volume'].mean()
        
        # Signal Logic
        is_bullish = last_price > last_ema9
        color = "#28a745" if is_bullish else "#dc3545"
        text = "STRATEGIC ALIGNMENT: BULLISH" if is_bullish else "STRATEGIC ALIGNMENT: BEARISH"
        
        return {
            "price": last_price, "ema9": last_ema9, "rvol": rvol, 
            "df": df, "ema_series": ema9_series, "color": color, "text": text
        }
    except:
        return None

# --- 3. SIDEBAR NAVIGATION ---
watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
st.sidebar.header("⚡ Momentum Scan")

# Use a selectbox for maximum stability against "None" errors
choice = st.sidebar.selectbox("Select Active Terminal", watchlist, 
                              index=watchlist.index(st.session_state.selected_ticker))

if choice != st.session_state.selected_ticker:
    st.session_state.selected_ticker = choice
    st.rerun()

# --- 4. MAIN TERMINAL ---
intel = get_clean_data(st.session_state.selected_ticker)

if intel:
    st.title(f"🛡️ {st.session_state.selected_ticker} Command")
    
    # Restored Logic Banner
    st.markdown(f'<div class="signal-banner" style="background-color:{intel["color"]};">⚠️ {intel["text"]}</div>', unsafe_allow_html=True)
    
    # Restored Metric Bar
    m1, m2, m3 = st.columns(3)
    m1.metric("Current Price", f"${intel['price']:.2f}")
    m2.metric("EMA 9 (Trend)", f"${intel['ema9']:.2f}", f"{(intel['price'] - intel['ema9']):+.2f}")
    m3.metric("RVOL", f"{intel['rvol']:.2f}x")

    # Restored Technical Chart (Price + EMA 9)
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(intel['df'].index, intel['df']['Close'], color='#0066cc', label='Price Action', linewidth=2)
    ax.plot(intel['ema_series'].index, intel['ema_series'], color='#28a745', label='EMA 9 (Trend)', linestyle='--', alpha=0.8)
    ax.set_facecolor('white'); fig.patch.set_facecolor('white')
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.legend(prop={'size': 8})
    st.pyplot(fig)

    # RISK SHIELD
    entry_price = intel['price']
    stop_loss = entry_price * 0.98 # Standard 2% Stop
    shares = 100 / (entry_price - stop_loss) # $100 Risk
    
    st.markdown(f"""
        <div class="risk-card">
            <span style="font-weight:bold; color:#856404;">🛡️ RISK SHIELD (Fixed $100 Risk)</span><br>
            <b>Buy:</b> {int(shares)} Shares | <b>Stop:</b> ${stop_loss:.2f} | <b>Total Position:</b> ${(shares * entry_price):.2f}
        </div>
    """, unsafe_allow_html=True)
else:
    # Error state to prevent white screen
    st.error("Market Data Connection Interrupted. Reconnecting...")
    if st.button("Manual Refresh"):
        st.rerun()
