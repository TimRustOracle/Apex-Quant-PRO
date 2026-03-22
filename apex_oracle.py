import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- 1. CORE BRAIN ---
st.set_page_config(layout="wide", page_title="Apex Restoration Suite", page_icon="🛡️")
st_autorefresh(interval=60 * 1000, key="momentum_sync")

if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "SOUN"

# Restoration Styling: Re-adding Color Coding
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1d23; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; min-width: 300px; }
    .momentum-container { margin-bottom: 12px; }
    .bar-bg { background: #eee; height: 10px; border-radius: 5px; overflow: hidden; margin-top: 4px; }
    .bar-fill { height: 100%; transition: width 0.8s ease; }
    .gold-glow { box-shadow: 0 0 15px #ffd700; border: 1.5px solid #ffd700 !important; }
    .risk-box { background: #fffbe6; padding: 12px; border-radius: 8px; border: 1.5px solid #ffe58f; }
    .prob-meter { background: #f0f7ff; padding: 12px; border-radius: 8px; border-left: 5px solid #004a99; border: 1px solid #d1e9ff; }
    div.stButton > button { width: 100%; border-radius: 4px; height: 45px; font-weight: bold; font-size: 0.75rem; color: white; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. RESTORED ENGINE ---
@st.cache_data(ttl=300)
def get_full_apex_metrics(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty: return None
        # Standardize Columns
        last = df.iloc[-1]; prev = df.iloc[-2]
        ema9_series = df['Close'].ewm(span=9, adjust=False).mean()
        ema9 = ema9_series.iloc[-1]
        rvol = last['Volume'] / df['Volume'].mean()
        change = ((last['Close'] - prev['Close']) / prev['Close']) * 100
        
        # Restore Apex Scoring Logic
        score = 0
        if last['Close'] > ema9: score += 50
        if rvol > 1.2: score += 50
        
        # Restore Color Logic
        color = "#dc3545" # Red
        if 50 <= score < 100: color = "#28a745" # Green
        if score >= 100: color = "#ffd700" # Gold
        
        return {"score": score, "color": color, "change": change, "price": last['Close'], "ema9": ema9, "rvol": rvol, "df": df, "ema_series": ema9_series}
    except: return None

# --- 3. SYNCED WATCHLIST ---
watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
processed = []
for t in watchlist:
    m = get_full_apex_metrics(t)
    if m: processed.append({"ticker": t, **m})

# Order: Hottest to Coldest
sorted_list = sorted(processed, key=lambda x: (x['score'], x['change']), reverse=True)
bullish_count = sum(1 for x in sorted_list if x['score'] >= 50)

# Sidebar Restoration
with st.sidebar:
    st.header("⚡ Hottest Momentum")
    ticker_names = [x['ticker'] for x in sorted_list]
    idx = ticker_names.index(st.session_state.selected_ticker) if st.session_state.selected_ticker in ticker_names else 0
    choice = st.radio("Active Terminal", ticker_names, index=idx)
    if choice != st.session_state.selected_ticker:
        st.session_state.selected_ticker = choice
        st.rerun()

    st.divider()
    for item in sorted_list:
        glow = "gold-glow" if item['color'] == "#ffd700" else ""
        st.markdown(f"""
            <div class="momentum-container">
                <div style="font-size:0.7rem; font-weight:bold;">{item['ticker']} <span style="float:right;">{item['score']}%</span></div>
                <div class="bar-bg {glow}"><div class="bar-fill" style="width:{item['score']}%; background-color:{item['color']};"></div></div>
            </div>
        """, unsafe_allow_html=True)

# --- 4. COMMAND CENTER RESTORATION ---
cur = st.session_state.selected_ticker
m_data = next((x for x in sorted_list if x['ticker'] == cur), None)

if m_data:
    st.title(f"🛡️ {cur} Command Center")
    
    # Restore Metric Row
    m1, m2, m3 = st.columns(3)
    m1.metric("Price", f"${m_data['price']:.2f}")
    m2.metric("EMA 9", f"${m_data['ema9']:.2f}", f"{(m_data['price'] - m_data['ema9']):+.2f}")
    m3.metric("RVOL", f"{m_data['rvol']:.2f}x")

    # Restore Technical Chart (Price + EMA 9)
    fig, ax = plt.subplots(figsize=(10, 2.5))
    ax.plot(m_data['df'].index, m_data['df']['Close'], color='#0066cc', label='Price Action', linewidth=1.5)
    ax.plot(m_data['ema_series'].index, m_data['ema_series'], color='#28a745', label='EMA 9 (Trend)', linestyle='--', alpha=0.8)
    ax.set_facecolor('white'); fig.patch.set_facecolor('white')
    ax.legend(prop={'size': 7})
    st.pyplot(fig)

    # Risk Shield & Prob Sync
    r_col, p_col = st.columns([2, 1])
    with r_col:
        price = m_data['price']
        stop = price * 0.98
        shares = 100 / (price - stop)
        st.markdown(f"""<div class="risk-box"><b>Risk Shield:</b> Buy {int(shares)} Shares | <b>Stop:</b> ${stop:.2f} | <b>Max Loss:</b> $100</div>""", unsafe_allow_html=True)
    with p_col:
        p_val = (bullish_count / len(watchlist)) * 100
        st.markdown(f"""<div class="prob-meter"><b>Probability:</b> {p_val:.0f}%</div>""", unsafe_allow_html=True)

    # Restore Sorted Heat Map with Color
    st.caption("Market Heat Map (Click to Sync)")
    h_cols = st.columns(len(sorted_list))
    for i, item in enumerate(sorted_list):
        btn_style = f"background-color: {item['color']}; color: {'black' if item['color'] == '#ffd700' else 'white'};"
        if h_cols[i].markdown(f'<div style="text-align:center;"><button style="{btn_style} border:none; border-radius:4px; padding:10px; width:100%; cursor:pointer;">{item["ticker"]}<br>{item["change"]:+.1f}%</button></div>', unsafe_allow_html=True):
             pass # Use buttons for visual consistency, sync via sidebar/session state
