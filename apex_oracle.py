import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- 1. CORE BRAIN ---
st.set_page_config(layout="wide", page_title="Apex Command Final", page_icon="🛡️")
st_autorefresh(interval=60 * 1000, key="momentum_sync")

# Self-Healing Selection Logic
if "selected_ticker" not in st.session_state or st.session_state.selected_ticker is None:
    st.session_state.selected_ticker = "SOUN"

# Unified "Pro" Styling
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1d23; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; min-width: 300px; }
    .risk-box { background: #fffbe6; padding: 12px; border-radius: 8px; border: 1.5px solid #ffe58f; }
    .prob-meter { background: #f0f7ff; padding: 12px; border-radius: 8px; border-left: 5px solid #004a99; border: 1px solid #d1e9ff; }
    .news-ticker { background: #1a1d23; color: #00ff00; padding: 10px; border-radius: 5px; font-family: 'Courier New', Courier, monospace; overflow: hidden; white-space: nowrap; }
    div.stButton > button { width: 100%; border-radius: 4px; height: 45px; font-weight: bold; font-size: 0.75rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE ---
@st.cache_data(ttl=300)
def get_clean_metrics(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="60d", interval="1d")
        if df.empty: return None
        last = df.iloc[-1]; prev = df.iloc[-2]
        ema9 = df['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
        change = ((last['Close'] - prev['Close']) / prev['Close']) * 100
        # Bullish Score Calculation
        score = 0
        if last['Close'] > ema9: score += 50
        if last['Volume'] > df['Volume'].mean(): score += 50
        color = "#ffd700" if score >= 100 else ("#28a745" if score >= 50 else "#dc3545")
        return {"score": score, "color": color, "change": change, "price": last['Close'], "ema9": ema9}
    except: return None

# --- 3. DYNAMIC SYNC & SORT ---
watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
processed = []
for t in watchlist:
    data = get_clean_metrics(t)
    if data: processed.append({"ticker": t, **data})

sorted_list = sorted(processed, key=lambda x: (x['score'], x['change']), reverse=True)
bullish_count = sum(1 for x in sorted_list if x['score'] >= 50)

# Sidebar with "Auto-Switch"
with st.sidebar:
    st.header("⚡ Hottest Momentum")
    ticker_names = [x['ticker'] for x in sorted_list]
    idx = ticker_names.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in ticker_names else 0
    choice = st.radio("Active Terminal", ticker_names, index=idx)
    if choice != st.session_state.selected_ticker:
        st.session_state.selected_ticker = choice
        st.rerun()

# --- 4. THE COMMAND TERMINAL ---
cur = st.session_state.selected_ticker
cur_metrics = next((x for x in sorted_list if x['ticker'] == cur), None)

if cur_metrics:
    st.title(f"🛡️ {cur} Strategic Command")
    
    # 60-Day Tech Chart
    df_chart = yf.download(cur, period="60d", progress=False)
    fig, ax = plt.subplots(figsize=(10, 2.2))
    ax.plot(df_chart.index, df_chart['Close'], color='#0066cc', linewidth=1.5)
    ax.set_facecolor('white'); fig.patch.set_facecolor('white')
    st.pyplot(fig)

    # RISK SHIELD & PROBABILITY
    risk_col, prob_col = st.columns([2, 1])
    with risk_col:
        price = cur_metrics['price']
        stop = price * 0.98  # 2% Risk Rule
        shares = 100 / (price - stop)
        st.markdown(f"""
            <div class="risk-box">
                <span style="font-size:0.75rem; font-weight:bold; color:#856404;">🛡️ RISK SHIELD (Max $100 Loss)</span><br>
                <b>Buy:</b> {int(shares)} Shares @ ${price:.2f} | <b>Stop:</b> ${stop:.2f} | <b>Total:</b> ${(shares*price):.2f}
            </div>
        """, unsafe_allow_html=True)

    with prob_col:
        p_val = (bullish_count / len(watchlist)) * 100
        st.markdown(f"""<div class="prob-meter"><div style="font-size:0.65rem; font-weight:bold;">PROBABILITY</div><div style="font-size:1.5rem; font-weight:900;">{p_val:.0f}%</div></div>""", unsafe_allow_html=True)

    # CLICKABLE HEAT MAP
    st.caption("Market Momentum Map (Click Stock to Sync)")
    h_cols = st.columns(len(sorted_list))
    for i, item in enumerate(sorted_list):
        if h_cols[i].button(f"{item['ticker']}\n{item['change']:+.1f}%", key=f"heat_{item['ticker']}"):
            st.session_state.selected_ticker = item['ticker']
            st.rerun()

    # Pinned Intelligence Feed
    st.divider()
    try:
        news = yf.Ticker(cur).news[0]
        st.markdown(f"""<div class="news-ticker">>> LATEST INTEL: {news['title']} -- SOURCE: {news['publisher']}</div>""", unsafe_allow_html=True)
    except:
        st.caption("Awaiting fresh market intelligence...")
