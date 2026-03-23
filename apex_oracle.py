import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import requests

# --- 1. PRO UI ARCHITECTURE ---
st.set_page_config(layout="wide", page_title="APEX COMMAND PRO")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #0a0a0a; border-right: 1px solid #1e1e1e; min-width: 420px !important; }
    .score-box { 
        width: 48px; height: 48px; border-radius: 6px; 
        display: flex; align-items: center; justify-content: center;
        font-weight: 900; font-size: 22px; margin-right: 15px; color: #000;
    }
    .ticker-card { 
        display: flex; align-items: center; padding: 12px; border-radius: 8px;
        margin-bottom: 10px; background: #121212; border: 1px solid #222;
    }
    .news-card {
        background: #0f0f0f; border-left: 5px solid #00e5ff;
        padding: 15px; border-radius: 4px; border: 1px solid #222;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE SCANNER & RATING ENGINE ---
@st.cache_data(ttl=60)
def run_power_scan():
    tickers = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST", "UPST"]
    results = []
    try:
        raw = yf.download(tickers + ["SPY"], period="10d", interval="1d", group_by='ticker', progress=False)
        spy_close = raw['SPY']['Close']
        spy_perf = (spy_close.iloc[-1] - spy_close.iloc[0]) / spy_close.iloc[0]

        for t in tickers:
            if t not in raw: continue
            df = raw[t].dropna()
            if len(df) < 2: continue
            
            price = float(df['Close'].iloc[-1])
            ema9 = df['Close'].ewm(span=9).mean().iloc[-1]
            rvol = df['Volume'].iloc[-1] / df['Volume'].mean()
            
            # 10-Point Rating Logic
            score = 0
            if 2.0 <= price <= 20.0: score += 2
            if price > ema9: score += 2
            if rvol > 1.5: score += 2
            if price > df['Close'].iloc[-2]: score += 1
            if rvol > 3.0: score += 1
            if ((price - df['Close'].iloc[0])/df['Close'].iloc[0]) > spy_perf: score += 1
            if abs(price - ema9)/price < 0.04: score += 1
            
            color = "#00ff41" if score >= 8 else "#ffea00" if score >= 5 else "#ff073a"
            results.append({"Ticker": t, "Price": price, "Score": score, "Color": color, "RVOL": rvol})
        return pd.DataFrame(results)
    except: return pd.DataFrame()

# --- 3. SIDEBAR RADAR ---
scan_data = run_power_scan()
target = None

with st.sidebar:
    st.markdown("### 📡 PRE-MARKET POWER SCAN")
    if not scan_data.empty:
        sorted_data = scan_data.sort_values(by="Score", ascending=False)
        for _, row in sorted_data.iterrows():
            st.markdown(f"""
                <div class="ticker-card">
                    <div class="score-box" style="background:{row['Color']};">{row['Score']}</div>
                    <div style="flex-grow:1;">
                        <span style="font-weight:bold; font-size:18px;">{row['Ticker']}</span><br>
                        <span style="color:#888; font-size:12px;">P: ${row['Price']:.2f} | RVOL: {row['RVOL']:.1f}x</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.divider()
        target = st.selectbox("ENGAGE FOCUS", sorted_data['Ticker'].tolist())
    else:
        st.error("Waiting for Market Data Sync...")

# --- 4. COMMAND DECK & CATALYST HUB ---
if target:
    st.title(f"🛡️ {target} // COMMAND DECK")
    hist = yf.download(target, period="60d", interval="1d", progress=False)
    
    if not hist.empty:
        # Charting Logic
        ema9 = hist['Close'].ewm(span=9).mean()
        fig = plt.figure(figsize=(14, 7), facecolor='#050505')
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])
        ax0 = plt.subplot(gs[0])
        ax0.plot(hist.index, hist['Close'], color='#FFFFFF', lw=2.5)
        ax0.plot(hist.index, ema9, color='#00e5ff', lw=1.5)
        ax0.set_facecolor('#050505')
        ax1 = plt.subplot(gs[1], sharex=ax0)
        ax1.bar(hist.index, hist['Volume'], color='#333')
        ax1.set_facecolor('#050505')
        plt.tight_layout()
        st.pyplot(fig)

        # Catalyst & Social Hub (Fixes the NameError)
        st.divider()
        st.subheader(f"🌪️ {target} CATALYST & SOCIAL HUB")
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("**REGULATORY NEWS**")
            news = yf.Ticker(target).news[:3]
            for n in news:
                st.markdown(f'<div class="news-card">{n["title"][:70]}...</div>', unsafe_allow_html=True)
        
        with c2:
            st.markdown("**SOCIAL SENTIMENT**")
            try:
                social = requests.get(f"https://api.stocktwits.com/api/2/streams/symbol/{target}.json", timeout=5).json()
                for m in social.get('messages', [])
