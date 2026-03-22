import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
import time

# --- 1. PRO ARCHITECTURE ---
st.set_page_config(layout="wide", page_title="APEX PRO COMMAND", page_icon="🛡️")
st_autorefresh(interval=120 * 1000, key="pro_sync") # Faster 2-min sync

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .status-banner { padding: 12px; border-radius: 4px; text-align: center; font-weight: bold; border: 1px solid #30363d; margin-bottom: 20px; }
    .stMetric { background: #161b22; border: 1px solid #30363d; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. RESILIENT ENGINE (Anti-Sync Error) ---
@st.cache_data(ttl=120)
def fetch_resilient_intel():
    # Targeted small-to-mid cap momentum list
    tickers = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST", "UPST"]
    valid_list = []
    
    try:
        # Fetch SPY first to establish connection
        spy = yf.download("SPY", period="5d", interval="1d", progress=False, timeout=10)
        spy_perf = (spy['Close'].iloc[-1] - spy['Close'].iloc[0]) / spy['Close'].iloc[0]
    except:
        spy_perf = 0 # Fallback if SPY fails

    for t in tickers:
        for attempt in range(2): # Force Reconnect Loop
            try:
                raw = yf.download(t, period="5d", interval="1d", progress=False, timeout=12)
                if not raw.empty and len(raw) >= 2:
                    last_p = float(raw['Close'].iloc[-1])
                    
                    # Strategic Filter: $2 to $30
                    if 2.0 <= last_p <= 30.0:
                        change = ((last_p - raw['Close'].iloc[-2]) / raw['Close'].iloc[-2]) * 100
                        rvol = raw['Volume'].iloc[-1] / raw['Volume'].mean()
                        stock_perf = (last_p - raw['Close'].iloc[0]) / raw['Close'].iloc[0]
                        rs_index = (stock_perf - spy_perf) * 100
                        
                        valid_list.append({
                            "Ticker": str(t), 
                            "Price": f"${last_p:.2f}",
                            "Change %": f"{change:+.2f}%",
                            "RVOL": round(float(rvol), 2),
                            "RS Index": round(float(rs_index), 2),
                            "Volume": f"{int(raw['Volume'].iloc[-1]):,}"
                        })
                    break # Success, move to next ticker
            except:
                time.sleep(1) # Brief pause before retry
                continue
    return pd.DataFrame(valid_list)

# --- 3. COMMAND INTERFACE ---
st.title("🛡️ APEX PRO COMMAND CENTER")

# SCANNER GRID
scan_df = fetch_resilient_intel()

if not scan_df.empty:
    st.subheader("📡 Live Momentum Scanner ($2-$30 Range)")
    # Sort by RVOL to find the biggest volume spikes
    st.dataframe(scan_df.sort_values(by="RVOL", ascending=False), use_container_width=True, hide_index=True)
    st.divider()

    # DEEP ANALYSIS
    col_nav, col_chart = st.columns([1, 3])
    
    with col_nav:
        st.subheader("Target Selection")
        target = st.selectbox("Select Active Ticker", scan_df['Ticker'].tolist())
        
        # Deep 60d pull for EMA 9 Strategy
        hist = yf.download(target, period="60d", interval="1d", progress=False, timeout=15)
        
        if not hist.empty:
            ema9 = hist['Close'].ewm(span=9, adjust=False).mean()
            price, ema = float(hist['Close'].iloc[-1]), float(ema9.iloc[-1])
            
            # PRO SIGNAL BANNER
            is_bullish = price > ema
            bg = "#238636" if is_bullish else "#da3633"
            label = "STRATEGIC ALIGNMENT: BULLISH" if is_bullish else "STRATEGIC ALIGNMENT: BEARISH"
            st.markdown(f'<div class="status-banner" style="background:{bg};">{label}</div>', unsafe_allow_html=True)
            
            # RISK SHIELD
            st.divider()
            stop = price * 0.98
            shares = 100 / (price - stop)
            st.info(f"🛡️ **RISK SHIELD ($100)**\n\nSize: {int(shares)} Shares\n\nStop: ${stop:.2f}")

    with col_chart:
        if not hist.empty:
            fig, ax = plt.subplots(figsize=(10, 4.2))
            ax.plot(hist.index, hist['Close'], color='#58a6ff', label='Price Action', lw=2)
            ax.plot(hist.index, ema9, color='#3fb950', label='EMA 9', ls='--', alpha=0.8)
            ax.set_facecolor('#0d1117')
            fig.patch.set_facecolor('#0d1117')
            ax.tick_params(colors='white')
            ax.grid(color='#30363d', linestyle='--', alpha=0.2)
            ax.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='white')
            st.pyplot(fig)
else:
    st.warning("📡 Market Syncing... The engine is forcing a reconnect. Please wait 10 seconds.")
    if st.button("Manual Force Refresh"):
        st.cache_data.clear()
        st.rerun()
