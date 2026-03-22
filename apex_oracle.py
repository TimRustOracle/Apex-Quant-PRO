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

# UI Styling: Sorting-Ready Layout
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1d23; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; min-width: 320px; }
    .momentum-container { margin-bottom: 15px; border-left: 3px solid transparent; padding-left: 5px; }
    .bar-bg { background: #eee; height: 10px; border-radius: 5px; overflow: hidden; margin-top: 4px; }
    .bar-fill { height: 100%; transition: width 0.8s ease; }
    .gold-glow { box-shadow: 0 0 20px #ffd700; border: 2px solid #ffd700 !important; }
    .heat-box { padding: 8px; border-radius: 5px; text-align: center; color: white; font-weight: bold; font-size: 0.75rem; border: 1px solid #ddd; }
    .prob-meter { background: #f1f3f5; padding: 15px; border-radius: 10px; border-left: 5px solid #004a99; }
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
    return {"score": score, "color": color, "change": change}

# --- 3. DYNAMIC SORTING LOGIC ---
raw_watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
processed_data = []

for t in raw_watchlist:
    metrics = get_apex_metrics(t)
    processed_data.append({"ticker": t, **metrics})

# Sort Hottest to Coldest based on Score, then Daily Change
sorted_watchlist = sorted(processed_data, key=lambda x: (x['score'], x['change']), reverse=True)
bullish_count = sum(1 for x in sorted_watchlist if x['score'] >= 40)

# --- 4. SIDEBAR: SYNCED & SORTED ---
with st.sidebar:
    st.header("⚡ Hottest Momentum")
    ticker_names = [x['ticker'] for x in sorted_watchlist]
    selected_ticker = st.radio("Active Terminal", ticker_names)
    st.divider()
    
    for item in sorted_watchlist:
        glow_style = "gold-glow" if item['color'] == "#ffd700" else ""
        st.markdown(f"""
            <div class="momentum-container">
                <div style="font-size:0.8rem; font-weight:bold;">{item['ticker']} <span style="float:right;">{item['score']}%</span></div>
                <div class="bar-bg {glow_style}">
                    <div class="bar-fill" style="width: {item['score']}%; background-color: {item['color']};"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# --- 5. MAIN COMMAND CENTER ---
st.title(f"🛡️ {selected_ticker} Pro Command")
main_df = get_market_data(selected_ticker)

if main_df is not None:
    main_df['ema9'] = main_df['close'].ewm(span=9, adjust=False).mean()
    last = main_df.iloc[-1]
    
    # Quick Stats
    m1, m2, m3 = st.columns(3)
    m1.metric("Price", f"${last['close']:.2f}")
    m2.metric("9-Day EMA", f"${last['ema9']:.2f}")
    m3.metric("RVOL", f"{(last['volume']/main_df['volume'].mean()):.1f}x")

    # ULTRA-COMPACT CHART
    fig, ax = plt.subplots(figsize=(10, 2.5)) 
    ax.plot(main_df.index, main_df['close'], color='#0066cc', label='Price Action', linewidth=1.5)
    ax.plot(main_df.index, main_df['ema9'], color='#28a745', label='EMA 9', linestyle='--')
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    ax.grid(color='#f1f3f5', linewidth=0.5)
    ax.legend(prop={'size': 7}, loc='upper right')
    ax.tick_params(labelsize=7)
    st.pyplot(fig)

    # SYNCED HEAT MAP & PROBABILITY
    prob_col, heat_col = st.columns([1, 2.5])
    
    with prob_col:
        prob_val = (bullish_count / len(sorted_watchlist)) * 100
        st.markdown(f"""
            <div class="prob-meter">
                <div style="font-size:0.75rem; font-weight:bold; color:#004a99;">BREAKOUT POTENTIAL</div>
                <div style="font-size:1.8rem; font-weight:900;">{prob_val:.0f}%</div>
                <div style="font-size:0.65rem; color:#666;">{bullish_count}/10 Stocks Bullishly Aligned</div>
            </div>
        """, unsafe_allow_html=True)

    with heat_col:
        st.caption("Sorted Market Velocity (Left = Hottest)")
        h_cols = st.columns(len(sorted_watchlist))
        for i, item in enumerate(sorted_watchlist):
            txt_col = "black" if item['color'] == "#ffd700" else "white"
            h_cols[i].markdown(f"""
                <div class="heat-box" style="background-color:{item['color']}; color:{txt_col};">
                    {item['ticker']}<br>{item['change']:+.1f}%
                </div>
            """, unsafe_allow_html=True)

    # AI INTEL
    st.divider()
    news = yf.Ticker(selected_ticker).news[:2]
    for n in news:
        h_text = n.get('title') or n.get('headline') or f"Intelligence for {selected_ticker}"
        with st.expander(f"🔹 {h_text[:95]}..."):
            st.write(h_text)
            st.caption(f"Source: {n.get('publisher', 'Financial Feed')} | [Link]({n.get('link', '#')})")
