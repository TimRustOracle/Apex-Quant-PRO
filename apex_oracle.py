import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import requests

# --- 1. TERMINAL UI SETUP ---
st.set_page_config(layout="wide", page_title="APEX COMMAND PRO", initial_sidebar_state="expanded")

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

# --- 2. MASTER SCANNER ENGINE ---
@st.cache_data(ttl=60)
def run_apex_scan():
    tickers = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST"]
    results = []
    try:
        raw = yf.download(tickers, period="5d", interval="1d", group_by='ticker', progress=False)
        for t in tickers:
            if t not in raw or raw[t].empty: continue
            df = raw[t].dropna()
            
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            ema9 = df['Close'].ewm(span=9).mean().iloc[-1]
            rvol = float(curr['Volume'] / df['Volume'].mean())
            
            # 10-Point Scoring
            score = 0
            if 2.0 <= curr['Close'] <= 25.0: score += 2
            if curr['Close'] > ema9: score += 2
            if rvol > 1.3: score += 2
            if curr['Close'] > prev['Close']: score += 2
            if rvol > 3.0: score += 2
            
            color = "#00ff41" if score >= 8 else "#ffea00" if score >= 5 else "#ff073a"
            results.append({"Ticker": t, "Price": round(curr['Close'], 2), "Score": int(score), "Color": color, "RVOL": round(rvol, 1)})
        return pd.DataFrame(results)
    except: return pd.DataFrame()

# --- 3. SIDEBAR RADAR ---
scan_df = run_apex_scan()
target = None

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
        target = st.selectbox("ENGAGE TERMINAL", sorted_df['Ticker'].tolist())

# --- 4. COMMAND DECK ---
if target:
    st.header(f"🛡️ {target} COMMAND DECK")
    hist = yf.download(target, period="60d", interval="1d", progress=False)
    
    if not hist.empty:
        ema9 = hist['Close'].ewm(span=9
