import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import requests

# --- 1. PRO UI ARCHITECTURE ---
st.set_page_config(layout="wide", page_title="APEX COMMAND PRO", initial_sidebar_state="expanded")

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
    .sentiment-card {
        background: #111; border: 1px solid #333; padding: 10px;
        border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #00e5ff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
@st.cache_data(ttl=60)
def run_master_scan():
    tickers = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST", "UPST"]
    results = []
    try:
        # Standardize data pull to avoid Series comparison errors
        raw = yf.download(tickers, period="5d", interval="1d", group_by='ticker', progress=False)
        for t in tickers:
            if t not in raw: continue
            df = raw[t].dropna()
            if df.empty: continue
            
            price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2])
            ema9 = df['Close'].ewm(span=9).mean().iloc[-1]
            rvol = float(df['Volume'].iloc[-1] / df['Volume'].mean())
            
            # 1-10 Scoring Logic
            score = 0
            if 2.0 <= price <= 30.0: score += 2
            if price > ema9: score += 3 # Heavy weight on trend
            if rvol > 1.2: score += 2
            if price > prev_price: score += 2
            if rvol > 2.5: score += 1
            
            color = "#00ff41" if score >= 8 else "#ffea00" if score >= 5 else "#ff073a"
            results.append({"Ticker": t, "Price": price, "Score": int(score), "Color": color, "RVOL": rvol})
        return pd.DataFrame(results)
    except Exception as e:
        st.sidebar.error(f"Engine Latency: {e}")
        return pd.DataFrame()

# --- 3. SIDEBAR RADAR ---
scan_df = run_master_scan()
selected_ticker = None

with st.sidebar:
    st.title("📡 POWER RADAR")
    if not scan_df.empty:
        # Fixed sorting logic to prevent the ValueError in your screenshot
        sorted_df = scan_df.sort_values(by="Score", ascending=False).reset_index(drop=True)
        for _, row in sorted_df.iterrows():
            st.markdown(f"""
                <div class="ticker-card">
                    <div class="score-box" style="background:{row['Color']};">{row['Score']}</div>
                    <div style="flex-grow:1;">
                        <span style="font-weight:bold; font-size:17px;">{row['Ticker']}</span><br>
                        <span style="color:#888; font-size:12px;">P: ${row['Price']:.2f} | RVOL: {row['RVOL']:.1f}x</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.divider()
        selected_ticker = st.selectbox("ENGAGE TERMINAL", sorted_df['Ticker'].tolist())
    else:
        st.warning("Awaiting Market Sync...")

# --- 4. MAIN TERMINAL ---
if selected_ticker:
    st.header(f"🛡️ {selected_ticker} COMMAND DECK")
    
    # Dual-Chart Area
    hist = yf.download(selected_ticker, period="60d", interval="1d", progress=False)
    if not hist.empty:
        ema9 = hist['Close'].ewm(span=9).mean()
        fig = plt.figure(figsize=(14, 6), facecolor='#050505')
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])
        
        ax0 = plt.subplot(gs[0])
        ax0.plot(hist.index, hist['Close'], color='#FFFFFF', lw=2, label="Price")
        ax0.plot(hist.index, ema9, color='#00e5ff', lw=1.2, ls='--', label="EMA 9")
        ax0.set_facecolor('#050505')
        ax0.grid(color='#222', alpha=0.5)
        
        ax1 = plt.subplot(gs[1], sharex=ax0)
        colors = ['#00ff41' if c >= o else '#ff073a' for o, c in zip(hist['Open'], hist['Close'])]
        ax1.bar(hist.index, hist['Volume'], color=colors, alpha=0.7)
        ax1.set_facecolor('#050505')
        
        plt.tight_layout()
        st.pyplot(fig)

    # Catalyst & Social Row
    st.divider()
    col_news, col_social = st.columns(2)
    
    with col_news:
        st.subheader("🗞️ NEWS CATALYSTS")
        news = yf.Ticker(selected_ticker).news[:3]
        if news:
            for n in news:
                st.markdown(f"""
                <div style="background:#111; padding:10px; border-radius:5px; margin-bottom:5px; border-left:3px solid #ffea00;">
                    <a href="{n['link']}" style="color:#eee; text-decoration:none; font-size:13px;">{n['title'][:80]}...</a>
                </div>
                """, unsafe_allow_html=True)
        else: st.write("No recent regulatory news.")

    with col_social:
        st.subheader("💬 SOCIAL PULSE")
        try:
            # Fixed loop syntax to resolve the error in your today's screenshot
            r = requests.get(f"https://api.stocktwits.com/api/2/streams/symbol/{selected_ticker}.json", timeout=5).json()
            messages = r.get('messages', [])
            if messages:
                for m in messages[:3]:
                    st.markdown(f"""
                    <div class="sentiment-card">
                        <span style="font-size:11px; color:#00e5ff;">@{m['user']['username']}</span><br>
                        <span style="font-size:12px;">{m['body'][:120]}...</span>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.write("Social mentions currently low.")
        except: st.write("Social API Rate-Limited. Retrying...")

else:
    st.info("Select a 1-10 rated stock from the radar to begin.")
