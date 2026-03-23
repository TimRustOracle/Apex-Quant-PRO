import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

# --- 1. PRO TERMINAL UI ---
st.set_page_config(layout="wide", page_title="APEX LIVE COMMAND")

# LIVE HEARTBEAT: This forces the page to refresh every 30 seconds
# Note: You may need to run 'pip install streamlit-autorefresh' in your terminal
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=30000, key="apex_heartbeat")
except:
    st.warning("Install 'streamlit-autorefresh' for automatic 30s updates.")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #0a0a0a; border-right: 1px solid #1e1e1e; min-width: 380px !important; }
    .score-box { 
        width: 42px; height: 42px; border-radius: 4px; 
        display: flex; align-items: center; justify-content: center;
        font-weight: 900; font-size: 18px; margin-right: 12px; color: #000;
    }
    .ticker-card { 
        display: flex; align-items: center; padding: 10px; border-radius: 6px;
        margin-bottom: 8px; background: #111; border: 1px solid #222;
    }
    .live-tag { color: #00ff41; font-size: 10px; font-weight: bold; border: 1px solid #00ff41; padding: 2px 5px; border-radius: 3px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE (1-MINUTE INTERVAL) ---
@st.cache_data(ttl=30)
def run_apex_live_scan():
    tickers = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST"]
    results = []
    try:
        # Fetching 1-minute data for the current session
        raw = yf.download(tickers, period="1d", interval="1m", group_by='ticker', progress=False)
        for t in tickers:
            if t not in raw or raw[t].empty: continue
            df = raw[t].dropna()
            if len(df) < 10: continue
            
            curr = df.iloc[-1]
            ema9 = df['Close'].ewm(span=9).mean().iloc[-1]
            # RVOL compared to the average of the last 100 minutes
            avg_vol = df['Volume'].tail(100).mean()
            rvol = float(curr['Volume'] / avg_vol) if avg_vol > 0 else 0
            
            score = 0
            if 2.0 <= curr['Close'] <= 25.0: score += 2
            if curr['Close'] > ema9: score += 2
            if rvol > 1.5: score += 2
            if curr['Close'] > df.iloc[-2]['Close']: score += 2
            if rvol > 3.0: score += 2
            
            color = "#00ff41" if score >= 8 else "#ffea00" if score >= 5 else "#ff073a"
            results.append({
                "Ticker": t, "Price": round(curr['Close'], 2), 
                "Score": int(score), "Color": color, "RVOL": round(rvol, 1)
            })
        return pd.DataFrame(results)
    except Exception as e:
        return pd.DataFrame()

# --- 3. SIDEBAR RADAR ---
scan_results = run_apex_live_scan()
focus_ticker = None

with st.sidebar:
    st.title("📡 LIVE RADAR")
    st.caption(f"Last Sync: {datetime.now().strftime('%H:%M:%S')}")
    if not scan_results.empty:
        sorted_df = scan_results.sort_values(by="Score", ascending=False)
        for _, row in sorted_df.iterrows():
            st.markdown(f"""
                <div class="ticker-card">
                    <div class="score-box" style="background:{row['Color']};">{row['Score']}</div>
                    <div style="flex-grow:1;">
                        <span style="font-weight:bold; font-size:16px;">{row['Ticker']}</span> <span class="live-tag">1M</span><br>
                        <span style="color:#888; font-size:11px;">P: ${row['Price']} | RVOL: {row['RVOL']}x</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.divider()
        focus_ticker = st.selectbox("ENGAGE TERMINAL", sorted_df['Ticker'].tolist())

# --- 4. THE COMMAND DECK ---
if focus_ticker:
    st.header(f"🛡️ {focus_ticker} // 1-MINUTE LIVE DECK")
    # Pulling 1-minute data for the chart
    hist = yf.download(focus_ticker, period="1d", interval="1m", progress=False)
    
    if not hist.empty:
        ema_line = hist['Close'].ewm(span=9).mean()
        
        # CHARTING
        fig, ax = plt.subplots(figsize=(14, 6), facecolor='#050505')
        ax.plot(hist.index, hist['Close'], color='#FFFFFF', lw=1.5, label="Price")
        ax.plot(hist.index, ema_line, color='#00e5ff', lw=1, ls='--', label="EMA 9")
        ax.set_facecolor('#050505')
        ax.grid(color='#1a1a1a', alpha=0.3)
        ax.tick_params(colors='#555', labelsize=8)
        st.pyplot(fig)

        # LIVE VOLUME
        st.caption("MINUTE-BY-MINUTE VOLUME VELOCITY")
        st.bar_chart(hist['Volume'].tail(60), color="#222222", height=150)
else:
    st.info("Radar scanning for momentum...")
