import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- 1. PRO SUITE CONFIG ---
st.set_page_config(layout="wide", page_title="APEX PRO COMMAND", page_icon="🛡️")
st_autorefresh(interval=120 * 1000, key="pro_sync") 

# Professional High-Density CSS
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    .status-banner { padding: 12px; border-radius: 4px; text-align: center; font-weight: bold; margin-bottom: 20px; border: 1px solid #30363d; }
    .metric-card { background: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 6px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PRO SCANNER ENGINE ($2-$30 Low Float Focus) ---
@st.cache_data(ttl=300)
def run_momentum_scanner():
    # Targeted small-mid cap momentum list
    tickers = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST", "MSTR", "UPST"]
    scan_results = []
    
    for t in tickers:
        try:
            # Multi-ticker fetch for efficiency
            data = yf.download(t, period="5d", interval="1d", progress=False, timeout=5)
            if data.empty: continue
            
            curr_price = float(data['Close'].iloc[-1])
            # Filter for Small/Mid Cap Price Range
            if 2.0 <= curr_price <= 30.0:
                avg_vol = data['Volume'].mean()
                curr_vol = data['Volume'].iloc[-1]
                rvol = curr_vol / avg_vol
                change = ((curr_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
                
                scan_results.append({
                    "Ticker": t, "Price": round(curr_price, 2),
                    "RVOL": round(rvol, 2), "Change %": round(change, 2), "Volume": int(curr_vol)
                })
        except: continue
    return pd.DataFrame(scan_results)

# --- 3. MAIN TERMINAL LOGIC ---
st.title("🛡️ APEX PRO COMMAND CENTER")

# SECTION 1: THE SCANNER GRID
st.subheader("📡 Live Momentum Scanner ($2-$30 Sweet Spot)")
raw_scan = run_momentum_scanner()

if not raw_scan.empty:
    # Rank by RVOL to find the low-float breakouts
    scanner_df = raw_scan.sort_values(by="RVOL", ascending=False)
    st.dataframe(scanner_df, use_container_width=True, hide_index=True)
    
    st.divider()

    # SECTION 2: DEEP TARGET ANALYSIS
    col_nav, col_chart = st.columns([1, 3])
    
    with col_nav:
        st.subheader("Target Selection")
        # Ensure selection is tied to a valid string to prevent ValueError
        target = st.selectbox("Select Scanned Ticker", scanner_df['Ticker'].tolist())
        
        # Fetching chart data only for the selected target
        intel = yf.download(target, period="60d", interval="1d", progress=False)
        
        if not intel.empty:
            ema9 = intel['Close'].ewm(span=9, adjust=False).mean()
            last_p = float(intel['Close'].iloc[-1])
            last_e = float(ema9.iloc[-1])
            
            # Logic Banner Restoration
            is_bullish = last_p > last_e
            bg_color = "#238636" if is_bullish else "#da3633"
            signal_text = "STRATEGIC ALIGNMENT: BULLISH" if is_bullish else "STRATEGIC ALIGNMENT: BEARISH"
            
            st.markdown(f'<div class="status-banner" style="background:{bg_color};">{signal_text}</div>', unsafe_allow_html=True)
            
            st.metric("Price", f"${last_p:.2f}", f"{(last_p - last_e):+.2f} vs EMA9")
            
            # Risk Shield calculation
            st.divider()
            stop = last_p * 0.98
            shares = 100 / (last_p - stop)
            st.info(f"🛡️ **RISK SHIELD ($100)**\n\nBuy: {int(shares)} Shares\n\nStop: ${stop:.2f}")

    with col_chart:
        if not intel.empty:
            fig, ax = plt.subplots(figsize=(10, 4.5))
            ax.plot(intel.index, intel['Close'], color='#58a6ff', label='Price Action', lw=2)
            ax.plot(intel.index, ema9, color='#3fb950', label='EMA 9 (Trend)', ls='--', alpha=0.8)
            
            # Pro Styling for Dark Mode
            ax.set_facecolor('#0d1117')
            fig.patch.set_facecolor('#0d1117')
            ax.tick_params(colors='white')
            ax.grid(color='#30363d', linestyle='--', alpha=0.3)
            ax.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='white')
            st.pyplot(fig)
else:
    st.warning("📡 Scanner searching for targets in the $2-$30 range. Checking market connectivity...")
