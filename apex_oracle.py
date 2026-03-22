import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- 1. PRO ARCHITECTURE & STYLING ---
st.set_page_config(layout="wide", page_title="APEX PRO COMMAND", page_icon="🛡️")
st_autorefresh(interval=180 * 1000, key="pro_sync") 

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .status-banner { padding: 12px; border-radius: 4px; text-align: center; font-weight: bold; border: 1px solid #30363d; margin-bottom: 20px; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PRE-MARKET SCANNER ENGINE ($2-$30 Focus) ---
@st.cache_data(ttl=300)
def fetch_pro_intel():
    # Targeted small-to-mid cap momentum list
    tickers = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST", "UPST"]
    valid_list = []
    
    # Benchmarking against S&P 500 for Relative Strength calculation
    spy = yf.download("SPY", period="5d", interval="1d", progress=False)['Close']
    spy_perf = (spy.iloc[-1] - spy.iloc[0]) / spy.iloc[0]

    for t in tickers:
        try:
            raw = yf.download(t, period="5d", interval="1d", progress=False, timeout=8)
            if raw.empty or len(raw) < 2: continue
            
            last_p = float(raw['Close'].iloc[-1])
            
            # Filter: Strategic Small-Cap Range
            if 2.0 <= last_p <= 30.0:
                change = ((last_p - raw['Close'].iloc[-2]) / raw['Close'].iloc[-2]) * 100
                rvol = raw['Volume'].iloc[-1] / raw['Volume'].mean()
                
                # Relative Strength Index (vs SPY)
                stock_perf = (last_p - raw['Close'].iloc[0]) / raw['Close'].iloc[0]
                rs_index = stock_perf - spy_perf
                
                valid_list.append({
                    "Ticker": str(t), 
                    "Price": f"${last_p:.2f}",
                    "Change %": f"{change:+.2f}%",
                    "RVOL": round(float(rvol), 2),
                    "RS Index": round(float(rs_index * 100), 2), # Leadership score
                    "Volume": f"{int(raw['Volume'].iloc[-1]):,}"
                })
        except: continue
    return pd.DataFrame(valid_list)

# --- 3. MAIN COMMAND INTERFACE ---
st.title("🛡️ APEX PRO COMMAND CENTER")

# SCANNER SECTION
st.subheader("📡 High-Momentum Pre-Scan ($2-$30 Low Float)")
master_df = fetch_pro_intel()

if not master_df.empty:
    # Sort by RS Index to see true market leaders
    st.dataframe(master_df.sort_values(by="RS Index", ascending=False), use_container_width=True, hide_index=True)
    st.divider()

    # DEEP ANALYSIS SECTION
    col_nav, col_chart = st.columns([1, 3])
    
    with col_nav:
        st.subheader("Target Focus")
        target = st.selectbox("Select Active Ticker", master_df['Ticker'].tolist())
        
        # Deep 60d pull for Strategy Execution
        hist = yf.download(target, period="60d", interval="1d", progress=False)
        
        if not hist.empty:
            ema9 = hist['Close'].ewm(span=9, adjust=False).mean()
            price, ema = float(hist['Close'].iloc[-1]), float(ema9.iloc[-1])
            
            # PRO SIGNAL BANNER
            is_bullish = price > ema
            bg = "#238636" if is_bullish else "#da3633"
            label = "STRATEGIC ALIGNMENT: BULLISH" if is_bullish else "STRATEGIC ALIGNMENT: BEARISH"
            st.markdown(f'<div class="status-banner" style="background:{bg};">{label}</div>', unsafe_allow_html=True)
            
            st.metric("Live Price", f"${price:.2f}", f"{price-ema:+.2f} vs EMA9")
            
            # RISK SHIELD
            st.divider()
            stop = price * 0.98
            shares = 100 / (price - stop)
            st.info(f"🛡️ **RISK SHIELD ($100)**\n\nSize: {int(shares)} Shares\n\nStop: ${stop:.2f}")

    with col_chart:
        if not hist.empty:
            fig, ax = plt.subplots(figsize=(10, 4.5))
            ax.plot(hist.index, hist['Close'], color='#58a6ff', label='Price Action', lw=2)
            ax.plot(hist.index, ema9, color='#3fb950', label='EMA 9 (Trend)', ls='--', alpha=0.8)
            
            # Pro Styling
            ax.set_facecolor('#0d1117')
            fig.patch.set_facecolor('#0d1117')
            ax.tick_params(colors='white')
            ax.grid(color='#30363d', linestyle='--', alpha=0.2)
            ax.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='white')
            st.pyplot(fig)
else:
    st.error("📡 Data Sync Failure: Please check market connectivity.")
