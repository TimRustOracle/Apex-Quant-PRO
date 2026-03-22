import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# --- 1. SETUP & CACHING ---
try:
    nltk.data.find('vader_lexicon')
except:
    nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()
st.set_page_config(layout="wide", page_title="Apex Golden Suite", page_icon="🛡️")
st_autorefresh(interval=60 * 1000, key="momentum_sync")

# Initialize State
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "SOUN"

# Styling for iMac High-Density View
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1d23; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; min-width: 320px; }
    .momentum-container { margin-bottom: 12px; }
    .bar-bg { background: #eee; height: 10px; border-radius: 5px; overflow: hidden; margin-top: 4px; }
    .bar-fill { height: 100%; transition: width 0.8s ease; }
    .gold-glow { box-shadow: 0 0 15px #ffd700; border: 1.5px solid #ffd700 !important; }
    .prob-meter { background: #f8f9fa; padding: 12px; border-radius: 8px; border-left: 4px solid #004a99; border: 1px solid #eee; }
    div.stButton > button { width: 100%; border-radius: 4px; height: 45px; font-weight: bold; font-size: 0.7rem; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CACHED ENGINE (Prevents RateLimitError) ---
@st.cache_data(ttl=300) # Cache for 5 mins to stay under rate limits
def get_clean_metrics(ticker):
    try:
        t_obj = yf.Ticker(ticker)
        df = t_obj.history(period="60d", interval="1d")
        if df.empty: return None
        
        last = df.iloc[-1]; prev = df.iloc[-2]
        ema9 = df['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
        rvol = last['Volume'] / df['Volume'].mean()
        change = ((last['Close'] - prev['Close']) / prev['Close']) * 100
        
        news = t_obj.news[:2]
        s_score = sum([sia.polarity_scores(n.get('title', ''))['compound'] for n in news]) / 2 if news else 0
        
        score = 0
        if last['Close'] > ema9: score += 40
        if rvol > 1.1: score += 30
        if s_score > 0.05: score += 30
        
        color = "#dc3545" # Red
        if 40 <= score < 90: color = "#28a745" # Green
        if score >= 90: color = "#ffd700" # Gold
        return {"score": score, "color": color, "change": change, "price": last['Close'], "ema9": ema9, "rvol": rvol}
    except: return None

# --- 3. DYNAMIC SORTING ---
watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
processed = []
for t in watchlist:
    m = get_clean_metrics(t)
    if m: processed.append({"ticker": t, **m})

sorted_list = sorted(processed, key=lambda x: (x['score'], x['change']), reverse=True)
bullish_count = sum(1 for x in sorted_list if x['score'] >= 40)

# --- 4. SIDEBAR: CLICKABLE SYNC ---
with st.sidebar:
    st.header("⚡ Hottest Momentum")
    ticker_names = [x['ticker'] for x in sorted_list]
    
    # Selection Sync
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

# --- 5. MAIN COMMAND CENTER ---
cur = st.session_state.selected_ticker
st.title(f"🛡️ {cur} Command")
m_data = next((x for x in sorted_list if x['ticker'] == cur), None)

if m_data:
    # Metrics Row
    m1, m2, m3 = st.columns(3)
    m1.metric("Price", f"${m_data['price']:.2f}")
    m2.metric("EMA 9", f"${m_data['ema9']:.2f}")
    m3.metric("RVOL", f"{m_data['rvol']:.1f}x")

    # Ultra-Compact View for iMac
    df_chart = yf.download(cur, period="60d", progress=False)
    fig, ax = plt.subplots(figsize=(10, 2.2)) 
    ax.plot(df_chart.index, df_chart['Close'], color='#0066cc', linewidth=1.2)
    ax.set_facecolor('white'); fig.patch.set_facecolor('white')
    ax.tick_params(labelsize=6)
    st.pyplot(fig)

    # CLICKABLE HEAT MAP & PROBABILITY
    prob_col, heat_col = st.columns([1, 3])
    with prob_col:
        p_val = (bullish_count / len(watchlist)) * 100
        st.markdown(f"""<div class="prob-meter"><div style="font-size:0.65rem;font-weight:bold;">PROBABILITY</div><div style="font-size:1.4rem;font-weight:900;">{p_val:.0f}%</div></div>""", unsafe_allow_html=True)

    with heat_col:
        h_cols = st.columns(len(sorted_list))
        for i, item in enumerate(sorted_list):
            if h_cols[i].button(f"{item['ticker']}\n{item['change']:+.1f}%", key=f"h_{item['ticker']}"):
                st.session_state.selected_ticker = item['ticker']
                st.rerun()

    # AI Intel Fallback
    st.divider()
    try:
        news_item = yf.Ticker(cur).news[0]
        st.info(f"💡 AI INTEL: {news_item.get('title', 'Market activity detected')}")
    except:
        st.caption("Seeking fresh intelligence...")
