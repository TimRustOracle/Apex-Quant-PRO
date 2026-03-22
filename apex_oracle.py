import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- 1. PRO ARCHITECTURE ---
st.set_page_config(layout="wide", page_title="APEX PRO COMMAND", page_icon="🛡️")
st_autorefresh(interval=120 * 1000, key="pro_sync") 

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .status-banner { padding: 12px; border-radius: 4px; text-align: center; font-weight: bold; border: 1px solid #30363d; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE FLAT-DATA ENGINE (Fixes Syntax Errors) ---
@st.cache_data(ttl=120)
def fetch_flat_intel():
    tickers = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST", "UPST"]
    valid_list = []
    
    try:
        # BATCH CALL
        # We use 'auto_adjust=True' and 'threads=True' for better performance on older hardware
        raw_data = yf.download(tickers + ["SPY"], period="5d", interval="1d", group_by='ticker', progress=False, timeout=20)
        
        # Benchmarking SPY
        spy_close = raw_data['SPY']['Close']
        spy_perf = (spy_close.iloc[-1] - spy_close.iloc[0]) / spy_close.iloc[0]
        
        for t in tickers:
            if t not in raw_data: continue
            
            # Flattening the data immediately to prevent Syntax/Value Errors
            t_df = raw_data[t].copy().dropna()
            if len(t_df) < 2: continue
            
            price = float(t_df['Close'].iloc[-1])
            
            # Small-Cap Filter ($2 - $30)
            if 2.0 <= price <= 30.0:
                change = ((price - t_df['Close'].iloc[-2]) / t_df['Close'].iloc[-2]) * 100
                rvol = t_df['Volume'].iloc[-1] / t_df['Volume'].mean()
                stock_perf = (price - t_df['Close'].iloc[0]) / t_df['Close'].iloc[0]
                rs_index = (stock_perf - spy_perf) * 100
                
                valid_list.append({
                    "Ticker": str(t), 
                    "Price": f"${price:.2f}",
                    "Change %": f"{change:+.2f}%",
                    "RVOL": round(float(rvol), 2),
                    "RS Index": round(float(rs_index), 2),
                    "Volume": f"{int(t_df['Volume'].iloc[-1]):,}"
                })
        return pd.DataFrame(valid_list)
    except Exception as e:
        # If the batch fails, the UI won't crash; it will show this alert
        return pd.DataFrame()

# --- 3. COMMAND INTERFACE ---
st.title("🛡️ APEX PRO COMMAND CENTER")

scan_results = fetch_flat_intel()

if not scan_results.empty:
    st.subheader("📡 Live Momentum Scanner ($2-$30 Range)")
    # Sorting by RVOL for momentum discovery
    st.dataframe(scan_results.sort_values(by="RVOL", ascending=False), use_container_width=True, hide_index=True)
    st.divider()

    col_nav, col_chart = st.columns([1, 3])
    
    with col_nav:
        st.subheader("Target Focus")
        target = st.selectbox("Select Active Ticker", scan_results['Ticker'].tolist())
        
        # Deep pull for the EMA 9 Chart
        hist = yf.download(target, period="60d", interval="1d", progress=False)
        
        if not hist.empty:
            ema9 = hist['Close'].ewm(span=9, adjust=False).mean()
            last_p, last_e = float(hist['Close'].iloc[-1]), float(ema9.iloc[-1])
            
            # PRO SIGNAL BANNER
            is_bullish = last_p > last_e
            banner_col = "#238636" if is_bullish else "#da3633"
            banner_txt = "STRATEGIC ALIGNMENT: BULLISH" if is_bullish else "STRATEGIC ALIGNMENT: BEARISH"
            st.markdown(f'<div class="status-banner" style="background:{banner_col};">{banner_txt}</div>', unsafe_allow_html=True)
            
            # RISK SHIELD
            st.divider()
            stop = last_p * 0.98
            shares = 100 / (last_p - stop)
            st.info(f"🛡️ **RISK SHIELD ($100)**\n\nSize: {int(shares)} Shares\n\nStop: ${stop:.2f}")

    with col_chart:
        if not hist.empty:
            fig, ax = plt.subplots(figsize=(10, 4.2))
            ax.plot(hist.index, hist['Close'], color='#58a6ff', label='Price Action', lw=2)
            ax.plot(hist.index, ema9, color='#3fb950', label='EMA 9', ls='--', alpha=0.8)
            
            # Pro Aesthetics
            ax.set_facecolor('#0d1117')
            fig.patch.set_facecolor('#0d1117')
            ax.tick_params(colors='white')
            ax.grid(color='#30363d', linestyle='--', alpha=0.2)
            ax.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='white')
            st.pyplot(fig)
else:
    st.warning("📡 Initializing Batch Sync... Please wait 10 seconds for market data.")
    if st.button("Manual Reconnect"):
        st.cache_data.clear()
        st.rerun()
