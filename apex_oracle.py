\import streamlit as st
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

# --- 2. THE BATCH ENGINE (Stops the Sync Error) ---
@st.cache_data(ttl=120)
def fetch_batch_intel():
    # Targeted small-to-mid cap momentum list
    tickers = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST", "UPST"]
    
    try:
        # BATCH CALL: One request for all tickers + SPY for Relative Strength
        all_data = yf.download(tickers + ["SPY"], period="5d", interval="1d", group_by='ticker', progress=False, timeout=20)
        
        spy_close = all_data['SPY']['Close']
        spy_perf = (spy_close.iloc[-1] - spy_close.iloc[0]) / spy_close.iloc[0]
        
        valid_list = []
        for t in tickers:
            if t not in all_data: continue
            t_data = all_data[t].dropna()
            if len(t_data) < 2: continue
            
            price = float(t_data['Close'].iloc[-1])
            
            # Filter: Strategic $2 to $30 Range
            if 2.0 <= price <= 30.0:
                change = ((price - t_data['Close'].iloc[-2]) / t_data['Close'].iloc[-2]) * 100
                rvol = t_data['Volume'].iloc[-1] / t_data['Volume'].mean()
                stock_perf = (price - t_data['Close'].iloc[0]) / t_data['Close'].iloc[0]
                rs_index = (stock_perf - spy_perf) * 100
                
                valid_list.append({
                    "Ticker": str(t), 
                    "Price": f"${price:.2f}",
                    "Change %": f"{change:+.2f}%",
                    "RVOL": round(float(rvol), 2),
                    "RS Index": round(float(rs_index), 2),
                    "Volume": f"{int(t_data['Volume'].iloc[-1]):,}"
                })
        return pd.DataFrame(valid_list)
    except Exception as e:
        st.error(f"Batch Sync Failed: {e}")
        return pd.DataFrame()

# --- 3. COMMAND INTERFACE ---
st.title("🛡️ APEX PRO COMMAND CENTER")

master_df = fetch_batch_intel()

if not master_df.empty:
    st.subheader("📡 Live Momentum Scanner ($2-$30 Range)")
    # Sort by RVOL to highlight high-volume low-float breakouts
    st.dataframe(master_df.sort_values(by="RVOL", ascending=False), use_container_width=True, hide_index=True)
    st.divider()

    col_nav, col_chart = st.columns([1, 3])
    
    with col_nav:
        st.subheader("Target Selection")
        target = st.selectbox("Select Active Ticker", master_df['Ticker'].tolist())
        
        # Focused daily pull for EMA 9 Strategy
        hist = yf.download(target, period="60d", interval="1d", progress=False)
        
        if not hist.empty:
            ema9 = hist['Close'].ewm(span=9, adjust=False).mean()
            price, ema = float(hist['Close'].iloc[-1]), float(ema9.iloc[-1])
            
            # PRO SIGNAL BANNER
            is_bullish = price > ema
            bg = "#238636" if is_bullish else "#da3633"
            label = "STRATEGIC ALIGNMENT: BULLISH" if is_bullish else "STRATEGIC ALIGNMENT: BEARISH"
            st.markdown(f'<div class="status-banner" style="background:{bg};">{label}</div>', unsafe_allow_html=True)
            
            # RISK SHIELD ($100 Account Protection)
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
    st.warning("📡 Market Syncing... The engine is switching to Batch Mode. Please wait.")
    if st.button("Force Reconnect"):
        st.cache_data.clear()
        st.rerun()
