import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- 1. CORE SETUP ---
st.set_page_config(layout="wide", page_title="Apex Risk Shield", page_icon="🛡️")
st_autorefresh(interval=60 * 1000, key="momentum_sync")

if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "SOUN"

# Unified UI Styling
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1d23; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; min-width: 300px; }
    .risk-box { background: #fffbe6; padding: 15px; border-radius: 10px; border: 1.5px solid #ffe58f; margin-top: 10px; }
    .prob-meter { background: #f0f7ff; padding: 15px; border-radius: 10px; border-left: 5px solid #004a99; }
    div.stButton > button { width: 100%; border-radius: 4px; height: 45px; font-weight: bold; font-size: 0.75rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
@st.cache_data(ttl=300)
def get_apex_data(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty: return None
        last = df.iloc[-1]; prev = df.iloc[-2]
        ema9 = df['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
        change = ((last['Close'] - prev['Close']) / prev['Close']) * 100
        # Simple Apex Scoring
        score = 0
        if last['Close'] > ema9: score += 50
        if last['Volume'] > df['Volume'].mean(): score += 50
        color = "#ffd700" if score >= 100 else ("#28a745" if score >= 50 else "#dc3545")
        return {"score": score, "color": color, "change": change, "price": last['Close'], "ema9": ema9}
    except: return None

# --- 3. DYNAMIC NAVIGATION ---
watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
processed = []
for t in watchlist:
    data = get_apex_data(t)
    if data: processed.append({"ticker": t, **data})

sorted_list = sorted(processed, key=lambda x: (x['score'], x['change']), reverse=True)
bullish_count = sum(1 for x in sorted_list if x['score'] >= 50)

with st.sidebar:
    st.header("⚡ Hottest Momentum")
    ticker_names = [x['ticker'] for x in sorted_list]
    idx = ticker_names.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in ticker_names else 0
    choice = st.radio("Active Terminal", ticker_names, index=idx)
    if choice != st.session_state.selected_ticker:
        st.session_state.selected_ticker = choice
        st.rerun()

# --- 4. MAIN COMMAND CENTER ---
cur = st.session_state.selected_ticker
st.title(f"🛡️ {cur} Apex Terminal")
cur_data = next((x for x in sorted_list if x['ticker'] == cur), None)

if cur_data:
    # CHART SECTION
    df_plot = yf.download(cur, period="60d", progress=False)
    fig, ax = plt.subplots(figsize=(10, 2.2))
    ax.plot(df_plot.index, df_plot['Close'], color='#0066cc', linewidth=1.5)
    ax.set_facecolor('white'); fig.patch.set_facecolor('white')
    st.pyplot(fig)

    # RISK & PROBABILITY ROW
    risk_col, prob_col = st.columns([2, 1])
    
    with risk_col:
        # RISK SHIELD CALCULATIONS
        entry = cur_data['price']
        stop_price = entry * 0.98 # 2% Stop Loss rule
        risk_per_share = entry - stop_price
        shares_to_buy = 100 / risk_per_share # Fixed $100 Risk
        
        st.markdown(f"""
            <div class="risk-box">
                <span style="color:#856404; font-weight:bold; font-size:0.8rem;">🛡️ RISK SHIELD (Fixed $100 Risk)</span><br>
                <div style="display:flex; justify-content:space-between; margin-top:5px;">
                    <div><b>Buy Size:</b> {int(shares_to_buy)} Shares</div>
                    <div><b>Stop Loss:</b> ${stop_price:.2f}</div>
                    <div><b>Total Capital:</b> ${(shares_to_buy * entry):.2f}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with prob_col:
        p_val = (bullish_count / len(watchlist)) * 100
        st.markdown(f"""
            <div class="prob-meter">
                <div style="font-size:0.65rem; font-weight:bold; color:#004a99;">PROBABILITY</div>
                <div style="font-size:1.6rem; font-weight:900;">{p_val:.0f}%</div>
            </div>
        """, unsafe_allow_html=True)

    # CLICKABLE HEAT MAP
    st.caption("Market Heat Map (Sorted Hottest to Coldest)")
    h_cols = st.columns(len(sorted_list))
    for i, item in enumerate(sorted_list):
        if h_cols[i].button(f"{item['ticker']}\n{item['change']:+.1f}%", key=f"h_{item['ticker']}"):
            st.session_state.selected_ticker = item['ticker']
            st.rerun()
