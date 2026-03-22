import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- 1. PRO SUITE CONFIG ---
st.set_page_config(layout="wide", page_title="APEX PRO COMMAND", page_icon="📈")
st_autorefresh(interval=180 * 1000, key="pro_sync") # 3-minute refresh for stability

# Professional Dark-Themed Styling
st.markdown("""
    <style>
    .reportview-container { background: #0e1117; }
    .metric-card { background: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 5px; }
    .status-bull { color: #238636; font-weight: bold; border-left: 4px solid #238636; padding-left: 10px; }
    .status-bear { color: #da3633; font-weight: bold; border-left: 4px solid #da3633; padding-left: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE SCANNER ENGINE (Small-to-Mid Cap Focus) ---
@st.cache_data(ttl=600)
def run_market_scanner():
    # Focused Watchlist for Small/Mid Cap Momentum
    tickers = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST", "MSTR", "UPST"]
    scan_results = []
    
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            # Fetching 5d for fast volume/float relative analysis
            hist = stock.history(period="5d")
            if hist.empty: continue
            
            curr_price = hist['Close'].iloc[-1]
            # Criteria: $2 to $20 range (Small/Mid Cap sweet spot)
            if 2.0 <= curr_price <= 30.0: 
                avg_vol = hist['Volume'].mean()
                curr_vol = hist['Volume'].iloc[-1]
                rvol = curr_vol / avg_vol
                change = ((curr_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                
                scan_results.append({
                    "Ticker": t,
                    "Price": round(curr_price, 2),
                    "RVOL": round(rvol, 2),
                    "Change %": round(change, 2),
                    "Volume": curr_vol
                })
        except: continue
    return pd.DataFrame(scan_results)

# --- 3. THE ANALYSIS ENGINE (Technical Deep-Dive) ---
def get_technical_intel(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        ema9 = df['Close'].ewm(span=9, adjust=False).mean()
        return {"df": df, "ema9": ema9, "last_price": df['Close'].iloc[-1], "last_ema": ema9.iloc[-1]}
    except: return None

# --- 4. MAIN INTERFACE: COMMAND CENTER ---
st.title("🛡️ APEX PRO COMMAND CENTER")

# TOP ROW: MARKET SCANNER
st.subheader("📡 Live Momentum Scanner ($2-$30 Range)")
scanner_df = run_market_scanner()
if not scanner_df.empty:
    # Highlight high RVOL stocks
    st.dataframe(scanner_df.sort_values(by="RVOL", ascending=False), use_container_width=True)
else:
    st.info("Scanner searching for targets...")

st.divider()

# BOTTOM SECTION: DUAL COLUMN ANALYSIS
col_nav, col_chart = st.columns([1, 3])

with col_nav:
    st.subheader("Target Focus")
    target = st.selectbox("Select Scanned Ticker", scanner_df['Ticker'].tolist() if not scanner_df.empty else ["SOUN"])
    intel = get_technical_intel(target)
    
    if intel:
        is_bullish = intel['last_price'] > intel['last_ema']
        status_class = "status-bull" if is_bullish else "status-bear"
        st.markdown(f"<div class='{status_class}'>{target} Signal: {'BULLISH' if is_bullish else 'BEARISH'}</div>", unsafe_allow_html=True)
        
        st.write(f"**Price:** ${intel['last_price']:.2f}")
        st.write(f"**EMA 9:** ${intel['last_ema']:.2f}")
        
        # Risk Shield
        st.divider()
        stop = intel['last_price'] * 0.98
        shares = 100 / (intel['last_price'] - stop)
        st.warning(f"**RISK SHIELD**\n\nRisk $100: Buy {int(shares)} @ ${stop:.2f} Stop")

with col_chart:
    if intel:
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(intel['df'].index, intel['df']['Close'], color='#58a6ff', label='Price Action', lw=2)
        ax.plot(intel['df'].index, intel['ema9'], color='#238636', label='EMA 9', ls='--', alpha=0.8)
        ax.set_facecolor('#0d1117')
        fig.patch.set_facecolor('#0d1117')
        ax.tick_params(colors='white')
        ax.legend()
        st.pyplot(fig)
