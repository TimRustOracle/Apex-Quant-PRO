import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# --- 1. CORE BRAIN ---
try:
    nltk.data.find('vader_lexicon')
except:
    nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()
st.set_page_config(layout="wide", page_title="Apex Golden Suite", page_icon="🛡️")
st_autorefresh(interval=60 * 1000, key="momentum_sync")

# Initialize Session State for Clicking
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "SOUN"

# Styling with "Clickable" Button CSS
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1d23; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; min-width: 320px; }
    .momentum-container { margin-bottom: 15px; }
    .bar-bg { background: #eee; height: 10px; border-radius: 5px; overflow: hidden; margin-top: 4px; }
    .bar-fill { height: 100%; transition: width 0.8s ease; }
    .gold-glow { box-shadow: 0 0 20px #ffd700; border: 2px solid #ffd700 !important; }
    .prob-meter { background: #f1f3f5; padding: 15px; border-radius: 10px; border-left: 5px solid #004a99; }
    /* Heat Map Button Styling */
    div.stButton > button {
        width: 100%;
        border-radius: 5px;
        height: 50px;
        font-weight: bold;
        color: white;
        border: 1px solid #ddd;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE ---
def get_market_data(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).lower() for c in df.columns]
        return df
    except: return None

def get_apex_metrics(ticker):
    df = get_market_data(ticker)
    if df is None: return {"score": 0, "color": "#dc3545", "change": 0}
    last = df.iloc[-1]; prev = df.iloc[-2]
    ema9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
    rvol = last['volume'] / df['volume'].mean()
    change = ((last['close'] - prev['close']) / prev['close']) * 100
    
    news = yf.Ticker(ticker).news[:2]
    s_score = sum([sia.polarity_scores(n.get('title', ''))['compound'] for n in news]) / 2 if news else 0
    
    score = 0
    if last['close'] > ema9: score += 40
    if rvol > 1.2: score += 30
    if s_score > 0.05: score += 30
    
    color = "#dc3545" # Red
    if 40 <= score < 90: color = "#28a745" # Green
    if score >= 90: color = "#ffd700" # Gold
    return {"score": score, "color": color, "change": change}

# --- 3. DYNAMIC SORTING ---
watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
processed_data = []
for t in watchlist:
    metrics = get_apex_metrics(t)
    processed_data.append({"ticker": t, **metrics})

sorted_list = sorted(processed_data, key=lambda x: (x['score'], x['change']), reverse=True)
bullish_count = sum(1 for x in sorted_list if x['score'] >= 40)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("⚡ Hottest Momentum")
    ticker_names = [x['ticker'] for x in sorted_list]
    # Sync radio with session state
    radio_index = ticker_names.index(st.session_state.selected_ticker)
    selected_from_sidebar = st.radio("Active Terminal", ticker_names, index=radio_index)
    
    # Update session state if sidebar changes
    if selected_from_sidebar != st.session_state.selected_ticker:
        st.session_state.selected_ticker = selected_from_sidebar
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
current_ticker = st.session_state.selected_ticker
st.title(f"🛡️ {current_ticker} Command")
main_df = get_market_data(current_ticker)

if main_df is not None:
    main_df['ema9'] = main_df['close'].ewm(span=9, adjust=False).mean()
    last = main_df.iloc[-1]
    
    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Price", f"${last['close']:.2f}")
    m2.metric("9-Day EMA", f"${last['ema9']:.2f}")
    m3.metric("RVOL", f"{(last['volume']/main_df['volume'].mean()):.1f}x")

    # Chart
    fig, ax = plt.subplots(figsize=(10, 2.3)) 
    ax.plot(main_df.index, main_df['close'], color='#0066cc', linewidth=1.5)
    ax.plot(main_df.index, main_df['ema9'], color='#28a745', linestyle='--')
    ax.set_facecolor('white'); fig.patch.set_facecolor('white')
    st.pyplot(fig)

    # CLICKABLE HEAT MAP & PROBABILITY
    prob_col, heat_col = st.columns([1, 2.5])
    with prob_col:
        prob_val = (bullish_count / len(watchlist)) * 100
        st.markdown(f"""<div class="prob-meter"><div style="font-size:0.7rem;">BREAKOUT POTENTIAL</div><div style="font-size:1.5rem; font-weight:900;">{prob_val:.0f}%</div></div>""", unsafe_allow_html=True)

    with heat_col:
        st.caption("Click to Switch Stock (Sorted Hottest to Coldest)")
        h_cols = st.columns(len(sorted_list))
        for i, item in enumerate(sorted_list):
            btn_label = f"{item['ticker']}\n{item['change']:+.1f}%"
            # Actual clickable buttons for the Heat Map
            if h_cols[i].button(btn_label, key=f"btn_{item['ticker']}"):
                st.session_state.selected_ticker = item['ticker']
                st.rerun()

    # AI Intel
    st.divider()
    news = yf.Ticker(current_ticker).news[:1]
    for n in news:
        h_text = n.get('title') or f"Update for {current_ticker}"
        st.info(f"💡 AI INTEL: {h_text}")
