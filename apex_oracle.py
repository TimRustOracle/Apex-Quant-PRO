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

# Clean White Aesthetic + Gold Glow Sliders
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1d23; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; min-width: 320px; }
    .momentum-container { margin-bottom: 15px; }
    .bar-bg { background: #eee; height: 8px; border-radius: 4px; overflow: hidden; margin-top: 4px; }
    .bar-fill { height: 100%; transition: width 0.6s ease; }
    .gold-glow { box-shadow: 0 0 12px #ffd700; border: 1px solid #ffd700; }
    h1, h2, h3 { color: #004a99 !important; font-size: 1.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE ---
def get_safe_data(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).lower() for c in df.columns]
        return df
    except: return None

def get_momentum_stats(ticker):
    df = get_safe_data(ticker)
    if df is None: return 0, "#dc3545"
    
    last = df.iloc[-1]
    ema9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
    rvol = last['volume'] / df['volume'].mean()
    
    # Sentiment Safety Check
    news = yf.Ticker(ticker).news[:5]
    s_score = sum([sia.polarity_scores(n.get('title', ''))['compound'] for n in news]) / 5 if news else 0
    
    score = 0
    if last['close'] > ema9: score += 40
    if rvol > 1.3: score += 30
    if s_score > 0.1: score += 30
    
    color = "#dc3545" # Red
    if 40 <= score < 90: color = "#28a745" # Green
    if score >= 90: color = "#ffd700" # Gold
    return score, color

# --- 3. SIDEBAR: MOMENTUM SLIDERS ---
with st.sidebar:
    st.header("⚡ Momentum Scan")
    watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
    
    selected_ticker = st.radio("Active View", watchlist)
    st.divider()
    
    for t in watchlist:
        val, col = get_momentum_stats(t)
        glow = "gold-glow" if col == "#ffd700" else ""
        st.markdown(f"""
            <div class="momentum-container">
                <div style="font-size:0.8rem; font-weight:bold;">{t} <span style="float:right;">{val}%</span></div>
                <div class="bar-bg {glow}">
                    <div class="bar-fill" style="width: {val}%; background-color: {col};"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# --- 4. MAIN TERMINAL: COMPACT VIEW ---
st.title(f"🛡️ {selected_ticker} Command Center")
data = get_safe_data(selected_ticker)

if data is not None:
    data['ema9'] = data['close'].ewm(span=9, adjust=False).mean()
    last = data.iloc[-1]
    
    # Pro Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Price", f"${last['close']:.2f}")
    m2.metric("9-Day EMA", f"${last['ema9']:.2f}")
    m3.metric("RVOL", f"{(last['volume']/data['volume'].mean()):.1f}x")

    # REDUCED CHART SIZE
    fig, ax = plt.subplots(figsize=(10, 3)) # Shortened height for iMac display
    ax.plot(data.index, data['close'], color='#0066cc', label='Price', linewidth=1.5)
    ax.plot(data.index, data['ema9'], color='#28a745', label='EMA 9', linestyle='--')
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    ax.grid(color='#f1f3f5', linewidth=0.5)
    ax.legend(prop={'size': 7})
    ax.tick_params(labelsize=7)
    st.pyplot(fig)

    # SECURE NEWS FEED
    st.subheader("📰 AI Intel")
    news_items = yf.Ticker(selected_ticker).news[:3]
    for n in news_items:
        title = n.get('title') or n.get('headline') or "Market Headlines"
        with st.expander(title[:80] + "..."):
            st.write(title)
            st.caption(f"[Source: {n.get('publisher', 'Financial Feed')}]({n.get('link', '#')})")
