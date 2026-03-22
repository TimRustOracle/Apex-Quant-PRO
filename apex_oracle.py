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

# Custom UI Styling
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1d23; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; min-width: 320px; }
    .momentum-container { margin-bottom: 15px; }
    .bar-bg { background: #eee; height: 10px; border-radius: 5px; overflow: hidden; margin-top: 4px; }
    .bar-fill { height: 100%; transition: width 0.8s ease; }
    .gold-glow { box-shadow: 0 0 20px #ffd700; border: 2px solid #ffd700 !important; }
    .heat-box { padding: 8px; border-radius: 5px; text-align: center; color: white; font-weight: bold; font-size: 0.75rem; border: 1px solid #ddd; }
    .prob-meter { background: #f1f3f5; padding: 15px; border-radius: 10px; border-left: 5px solid #004a99; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE ---
def get_market_data(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).lower() for c in df.columns]
        return df
    except: return None

def get_apex_score(ticker):
    df = get_market_data(ticker)
    if df is None: return 0, "#dc3545", 0
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    ema9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
    rvol = last['volume'] / df['volume'].mean()
    change = ((last['close'] - prev['close']) / prev['close']) * 100
    
    news = yf.Ticker(ticker).news[:3]
    s_score = sum([sia.polarity_scores(n.get('title', ''))['compound'] for n in news]) / 3 if news else 0
    
    score = 0
    if last['close'] > ema9: score += 40
    if rvol > 1.2: score += 30
    if s_score > 0.05: score += 30
    
    color = "#dc3545" # Red
    if 40 <= score < 90: color = "#28a745" # Green
    if score >= 90: color = "#ffd700" # Gold
    return score, color, change

# --- 3. SIDEBAR & WATCHLIST ---
watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
heat_results = []
bullish_count = 0

with st.sidebar:
    st.header("⚡ Momentum Scan")
    selected_ticker = st.radio("Active View", watchlist)
    st.divider()
    
    for t in watchlist:
        val, col, chg = get_apex_score(t)
        heat_results.append({"t": t, "c": col, "p": chg})
        if val >= 40: bullish_count += 1 # Track bullish sentiment for Probability Meter
        
        glow_style = "gold-glow" if col == "#ffd700" else ""
        st.markdown(f"""
            <div class="momentum-container">
                <div style="font-size:0.8rem; font-weight:bold;">{t} <span style="float:right;">{val}%</span></div>
                <div class="bar-bg {glow_style}">
                    <div class="bar-fill" style="width: {val}%; background-color: {col};"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# --- 4. MAIN COMMAND CENTER ---
st.title(f"🛡️ {selected_ticker} Command Center")
data = get_market_data(selected_ticker)

if data is not None:
    data['ema9'] = data['close'].ewm(span=9, adjust=False).mean()
    last = data.iloc[-1]
    
    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Price", f"${last['close']:.2f}")
    m2.metric("9-Day EMA", f"${last['ema9']:.2f}")
    m3.metric("RVOL", f"{(last['volume']/data['volume'].mean()):.1f}x")

    # THE ULTRA-COMPACT CHART
    fig, ax = plt.subplots(figsize=(10, 2.5)) 
    ax.plot(data.index, data['close'], color='#0066cc', label='Price Action', linewidth=1.5)
    ax.plot(data.index, data['ema9'], color='#28a745', label='EMA 9', linestyle='--')
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    ax.grid(color='#f1f3f5', linewidth=0.5)
    ax.legend(prop={'size': 7}, loc='upper right')
    ax.tick_params(labelsize=7)
    st.pyplot(fig)

    # BREAKOUT PROBABILITY & HEAT MAP
    prob_col, heat_col = st.columns([1, 2.5])
    
    with prob_col:
        prob_val = (bullish_count / len(watchlist)) * 100
        st.markdown(f"""
            <div class="prob-meter">
                <div style="font-size:0.75rem; font-weight:bold; color:#004a99;">BREAKOUT POTENTIAL</div>
                <div style="font-size:1.8rem; font-weight:900;">{prob_val:.0f}%</div>
                <div style="font-size:0.65rem; color:#666;">{bullish_count}/10 Stocks Bullishly Aligned</div>
            </div>
        """, unsafe_allow_html=True)

    with heat_col:
        st.caption("Sector Momentum Map")
        h_cols = st.columns(len(watchlist))
        for i, res in enumerate(heat_results):
            bg = res['c']
            txt_col = "black" if bg == "#ffd700" else "white"
            h_cols[i].markdown(f"""
                <div class="heat-box" style="background-color:{bg}; color:{txt_col};">
                    {res['t']}<br>{res['p']:+.1f}%
                </div>
            """, unsafe_allow_html=True)

    # AI INTEL
    st.divider()
    raw_news = yf.Ticker(selected_ticker).news[:2]
    for n in raw_news:
        h_text = n.get('title') or n.get('headline') or f"Intelligence for {selected_ticker}"
        with st.expander(f"🔹 {h_text[:90]}..."):
            st.write(h_text)
            st.caption(f"Source: {n.get('publisher', 'Market Feed')} | [Full Intel]({n.get('link', '#')})")
