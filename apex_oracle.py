import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import requests

# --- 1. UI ARCHITECTURE ---
st.set_page_config(layout="wide", page_title="APEX COMMAND PRO")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #0a0a0a; border-right: 1px solid #1e1e1e; min-width: 400px !important; }
    .score-box { 
        width: 48px; height: 48px; border-radius: 6px; 
        display: flex; align-items: center; justify-content: center;
        font-weight: 900; font-size: 22px; margin-right: 15px; color: #000;
    }
    .ticker-card { 
        display: flex; align-items: center; padding: 12px; border-radius: 8px;
        margin-bottom: 10px; background: #121212; border: 1px solid #222;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE ---
@st.cache_data(ttl=60)
def run_apex_scan():
    tickers = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST"]
    results = []
    try:
        raw = yf.download(tickers, period="5d", interval="1d", group_by='ticker', progress=False)
        for t in tickers:
            if t not in raw or raw[t].empty: continue
            df = raw[t].dropna()
            if len(df) < 2: continue
            
            curr = df.iloc[-1]
            ema9_val = df['Close'].ewm(span=9).mean().iloc[-1]
            rvol = float(curr['Volume'] / df['Volume'].mean())
            
            score = 0
            if 2.0 <= curr['Close'] <= 25.0: score += 2
            if curr['Close'] > ema9_val: score += 2
            if rvol > 1.3: score += 2
            if curr['Close'] > df.iloc[-2]['Close']: score += 2
            if rvol > 3.0: score += 2
            
            color = "#00ff41" if score >= 8 else "#ffea00" if score >= 5 else "#ff073a"
            results.append({"Ticker": t, "Price": round(curr['Close'], 2), "Score": int(score), "Color": color, "RVOL": round(rvol, 1)})
        return pd.DataFrame(results)
    except: return pd.DataFrame()

# --- 3. SIDEBAR RADAR ---
scan_df = run_apex_scan()
target_ticker = None

with st.sidebar:
    st.title("📡 POWER RADAR")
    if not scan_df.empty:
        sorted_df = scan_df.sort_values(by="Score", ascending=False)
        for _, row in sorted_df.iterrows():
            st.markdown(f"""
                <div class="ticker-card">
                    <div class="score-box" style="background:{row['Color']};">{row['Score']}</div>
                    <div style="flex-grow:1;">
                        <span style="font-weight:bold; font-size:17px;">{row['Ticker']}</span><br>
                        <span style="color:#888; font-size:12px;">P: ${row['Price']} | RVOL: {row['RVOL']}x</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.divider()
        target_ticker = st.selectbox("ENGAGE TERMINAL", sorted_df['Ticker'].tolist())

# --- 4. THE COMMAND DECK ---
if target_ticker:
    st.header(f"🛡️ {target_ticker} COMMAND DECK")
    hist = yf.download(target_ticker, period="60d", interval="1d", progress=False)
    
    if not hist.empty:
        ema9 = hist['Close'].ewm(span=9).mean()
        
        # --- ROBUST CHARTING ENGINE ---
        fig = plt.figure(figsize=(14, 8), facecolor='#050505')
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])
        
        # Price/EMA Chart
        ax0 = plt.subplot(gs[0])
        ax0.plot(hist.index, hist['Close'], color='#FFFFFF', lw=2, label="Price")
        ax0.plot(hist.index, ema9, color='#00e5ff', lw=1.2, ls='--', label="EMA 9")
        ax0.set_facecolor('#050505')
        ax0.grid(color='#1a1a1a', alpha=0.5)
        
        # Volume Chart - New Loop Method to Kill the TypeError
        ax1 = plt.subplot(gs[1], sharex=ax0)
        # Instead of passing a list, we plot bars individually or use a safer mapping
        v_colors = ['#00ff41' if c >= o else '#ff073a' for o, c in zip(hist['Open'], hist['Close'])]
        ax1.bar(hist.index, hist['Volume'], color=v_colors, width=0.7)
        ax1.set_facecolor('#050505')
        ax1.grid(color='#1a1a1a', alpha=0.5)
        
        plt.tight_layout()
        st.pyplot(fig)

        # Bottom Row
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🗞️ NEWS")
            try:
                for n in yf.Ticker(target_ticker).news[:3]:
                    st.info(f"{n['title']}")
            except: st.write("Scanning news...")
        with c2:
            st.subheader("💬 SOCIAL")
            try:
                r = requests.get(f"https://api.stocktwits.com/api/2/streams/symbol/{target_ticker}.json", timeout=5).json()
                for m in r.get('messages', [])[:3]:
                    st.success(f"@{m['user']['username']}: {m['body'][:100]}")
            except: st.write("Syncing social feed...")
else:
    st.info("Select a ticker from the Power Radar.")
