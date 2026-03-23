import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests

# --- 1. PRO TERMINAL UI ---
st.set_page_config(layout="wide", page_title="APEX COMMAND PRO")

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
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE ---
@st.cache_data(ttl=60)
def run_apex_engine():
    tickers = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST"]
    results = []
    try:
        raw = yf.download(tickers, period="5d", interval="1d", group_by='ticker', progress=False)
        for t in tickers:
            if t not in raw or raw[t].empty: continue
            df = raw[t].dropna()
            if len(df) < 2: continue
            
            curr = df.iloc[-1]
            ema9 = df['Close'].ewm(span=9).mean().iloc[-1]
            rvol = float(curr['Volume'] / df['Volume'].mean())
            
            # 1-10 Scoring Logic
            score = 0
            if 2.0 <= curr['Close'] <= 25.0: score += 2
            if curr['Close'] > ema9: score += 2
            if rvol > 1.3: score += 2
            if curr['Close'] > df.iloc[-2]['Close']: score += 2
            if rvol > 3.0: score += 2
            
            color = "#00ff41" if score >= 8 else "#ffea00" if score >= 5 else "#ff073a"
            results.append({"Ticker": t, "Price": round(curr['Close'], 2), "Score": int(score), "Color": color, "RVOL": round(rvol, 1)})
        return pd.DataFrame(results)
    except: return pd.DataFrame()

# --- 3. SIDEBAR RADAR ---
scan_results = run_apex_engine()
focus_ticker = None

with st.sidebar:
    st.title("📡 POWER RADAR")
    if not scan_results.empty:
        sorted_df = scan_results.sort_values(by="Score", ascending=False)
        for _, row in sorted_df.iterrows():
            st.markdown(f"""
                <div class="ticker-card">
                    <div class="score-box" style="background:{row['Color']};">{row['Score']}</div>
                    <div style="flex-grow:1;">
                        <span style="font-weight:bold; font-size:16px;">{row['Ticker']}</span><br>
                        <span style="color:#888; font-size:11px;">P: ${row['Price']} | RVOL: {row['RVOL']}x</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.divider()
        focus_ticker = st.selectbox("ENGAGE TERMINAL", sorted_df['Ticker'].tolist())
    
    # NEW: Quick Risk Sizer
    st.divider()
    st.subheader("⚖️ POSITION SIZER")
    risk_amt = st.number_input("Risk Amount ($)", value=100)
    stop_dist = st.slider("Stop Loss %", 1, 10, 5)
    if focus_ticker:
        price = scan_results[scan_results['Ticker']==focus_ticker]['Price'].values[0]
        shares = int(risk_amt / (price * (stop_dist/100)))
        st.code(f"BUY: {shares} SHARES\nCOST: ${shares * price:,.2f}")

# --- 4. THE COMMAND DECK ---
if focus_ticker:
    st.header(f"🛡️ {focus_ticker} COMMAND DECK")
    hist = yf.download(focus_ticker, period="60d", interval="1d", progress=False)
    
    if not hist.empty:
        # Price Action Panel
        ema_val = hist['Close'].ewm(span=9).mean()
        fig, ax = plt.subplots(figsize=(14, 5), facecolor='#050505')
        ax.plot(hist.index, hist['Close'], color='#FFFFFF', lw=2, label="Price")
        ax.plot(hist.index, ema_val, color='#00e5ff', lw=1.2, ls='--', label="EMA 9")
        ax.set_facecolor('#050505')
        ax.grid(color='#1a1a1a', alpha=0.4)
        ax.tick_params(colors='#666')
        st.pyplot(fig)

        # Volume Panel
        st.bar_chart(hist['Volume'], color="#333333", height=150)

        # NEW: Optimized Catalyst & Social Row
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🗞️ LATEST CATALYSTS")
            try:
                news_items = yf.Ticker(focus_ticker).news[:4]
                for n in news_items:
                    st.markdown(f"▸ **{n['publisher']}**: [{n['title']}]({n['link']})")
            except: st.write("Scanning for regulatory news...")
        
        with c2:
            st.subheader("💬 SOCIAL SENTIMENT")
            try:
                r = requests.get(f"https://api.stocktwits.com/api/2/streams/symbol/{focus_ticker}.json", timeout=5).json()
                for m in r.get('messages', [])[:3]:
                    st.caption(f"**@{m['user']['username']}**: {m['body'][:120]}...")
            except: st.write("Sentiment stream unavailable.")
else:
    st.info("Select a ticker from the Power Radar to begin.")
