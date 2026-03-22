import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- 1. PRO SUITE ARCHITECTURE ---
st.set_page_config(layout="wide", page_title="APEX PRO COMMAND", page_icon="🛡️")
st_autorefresh(interval=180 * 1000, key="pro_sync") 

# High-Density Pro UI Styling
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .status-banner { padding: 12px; border-radius: 4px; text-align: center; font-weight: bold; border: 1px solid #30363d; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VALIDATED SCANNER ENGINE ($2-$30 Low Float) ---
@st.cache_data(ttl=300)
def fetch_validated_intel():
    tickers = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST", "UPST"]
    valid_list = []
    
    for t in tickers:
        try:
            # Multi-day pull to ensure we have valid float/volume data
            raw = yf.download(t, period="5d", interval="1d", progress=False, timeout=8)
            if raw.empty or len(raw) < 2: continue
            
            # Use .iloc[-1] and force to float to prevent the "Labeled Series" ValueError
            price = float(raw['Close'].iloc[-1])
            
            # Strategic Filter: $2 to $30 Small-Cap Focus
            if 2.0 <= price <= 30.0:
                avg_vol = raw['Volume'].mean()
                curr_vol = raw['Volume'].iloc[-1]
                rvol = curr_vol / avg_vol
                change = ((price - raw['Close'].iloc[-2]) / raw['Close'].iloc[-2]) * 100
                
                valid_list.append({
                    "Ticker": str(t), 
                    "Price": round(price, 2),
                    "RVOL": round(float(rvol), 2), 
                    "Change %": round(float(change), 2), 
                    "Volume": int(curr_vol)
                })
        except: continue
    return pd.DataFrame(valid_list)

# --- 3. MAIN COMMAND INTERFACE ---
st.title("🛡️ APEX PRO COMMAND CENTER")

# SECTION 1: THE SCANNER GRID
st.subheader("📡 Live Momentum Scanner ($2-$30 Sweet Spot)")
scan_results = fetch_validated_intel()

if not scan_results.empty:
    # Sorting is now safe because all values are validated floats
    final_grid = scan_results.sort_values(by="RVOL", ascending=False)
    st.dataframe(final_grid, use_container_width=True, hide_index=True)
    st.divider()

    # SECTION 2: DEEP TARGET FOCUS
    col_nav, col_chart = st.columns([1, 3])
    
    with col_nav:
        st.subheader("Target Focus")
        target = st.selectbox("Select Active Ticker", final_grid['Ticker'].tolist())
        
        # Deep 60d pull for the EMA 9 Strategy
        chart_data = yf.download(target, period="60d", interval="1d", progress=False)
        
        if not chart_data.empty:
            ema9 = chart_data['Close'].ewm(span=9, adjust=False).mean()
            last_p = float(chart_data['Close'].iloc[-1])
            last_e = float(ema9.iloc[-1])
            
            # PRO SIGNAL BANNER
            is_bullish = last_p > last_e
            bg = "#238636" if is_bullish else "#da3633"
            label = "STRATEGIC ALIGNMENT: BULLISH" if is_bullish else "STRATEGIC ALIGNMENT: BEARISH"
            st.markdown(f'<div class="status-banner" style="background:{bg};">{label}</div>', unsafe_allow_html=True)
            
            # Risk Shield calculation
            st.divider()
            stop = last_p * 0.98
            shares = 100 / (last_p - stop)
            st.info(f"🛡️ **RISK SHIELD ($100)**\n\nBuy: {int(shares)} Shares\n\nStop Loss: ${stop:.2f}")

    with col_chart:
        if not chart_data.empty:
            fig, ax = plt.subplots(figsize=(10, 4.5))
            ax.plot(chart_data.index, chart_data['Close'], color='#58a6ff', label='Price Action', lw=2)
            ax.plot(chart_data.index, ema9, color='#3fb950', label='EMA 9', ls='--', alpha=0.8)
            
            # Dark Mode Pro Aesthetics
            ax.set_facecolor('#0d1117')
            fig.patch.set_facecolor('#0d1117')
            ax.tick_params(colors='white')
            ax.grid(color='#30363d', linestyle='--', alpha=0.3)
            ax.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='white')
            st.pyplot(fig)
else:
    st.warning("📡 Scanner searching for targets in the $2-$30 range. Check your internet connection if this persists.")
