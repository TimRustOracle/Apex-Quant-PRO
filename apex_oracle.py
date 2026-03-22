import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# --- 1. BRAIN INITIALIZATION ---
try:
    nltk.data.find('vader_lexicon')
except:
    nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()
st.set_page_config(layout="wide", page_title="Apex Golden Terminal", page_icon="🛡️")
st_autorefresh(interval=60 * 1000, key="momentum_sync")

# Custom CSS for the "Gold Glow" and White Theme
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1d23; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; min-width: 350px; }
    .momentum-container { margin-bottom: 20px; padding: 5px; }
    .momentum-label { display: flex; justify-content: space-between; font-weight: bold; font-size: 0.85rem; }
    .bar-bg { background: #eee; height: 12px; border-radius: 6px; overflow: hidden; margin-top: 4px; border: 1px solid #ddd; }
    .bar-fill { height: 100%; transition: width 0.5s ease; }
    .gold-glow { box-shadow: 0 0 15px #ffd700; border: 2px solid #ffd700 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE MOMENTUM ENGINE ---
def get_stock_data(ticker, period="60d", interval="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).lower() for c in df.columns]
        return df
    except: return None

def calculate_score(ticker):
    df = get_stock_data(ticker)
    if df is None: return 0, "#dc3545"
    
    # Technicals
    last_price = df['close'].iloc[-1]
    ema9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
    rvol = df['volume'].iloc[-1] / df['volume'].mean()
    
    # Sentiment
    news = yf.Ticker(ticker).news[:5]
    s_score = sum([sia.polarity_scores(n.get('title', ''))['compound'] for n in news]) / 5 if news else 0
    
    # Logic: Red -> Green -> Gold
    score = 0
    if last_price > ema9: score += 40
    if rvol > 1.2: score += 30
    if s_score > 0.1: score += 30
    
    color = "#dc3545" # Red (Weak)
    if 40 <= score < 90: color = "#28a745" # Green (Strong)
    if score >= 90: color = "#ffd700" # Gold (Apex)
    
    return score, color

# --- 3. SIDEBAR B: HEAT-MAP SLIDERS ---
with st.sidebar:
    st.header("⚡ Momentum Scan")
    st.caption("$2 - $20 Velocity Watchlist")
    
    watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
    
    # Radio for selection
    selected_ticker = st.radio("Active Terminal", watchlist, label_visibility="collapsed")
    
    st.divider()
    for t in watchlist:
        m_val, m_col = calculate_score(t)
        glow_class = "gold-glow" if m_col == "#ffd700" else ""
        
        st.markdown(f"""
            <div class="momentum-container">
                <div class="momentum-label"><span>{t}</span><span>{m_val}%</span></div>
                <div class="bar-bg {glow_class}">
                    <div class="bar-fill" style="width: {m_val}%; background-color: {m_col};"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# --- 4. MAIN TERMINAL: COMPACT VIEW ---
st.title(f"🛡️ {selected_ticker} Pro Command")
main_df = get_stock_data(selected_ticker)

if main_df is not None:
    main_df['ema9'] = main_df['close'].ewm(span=9, adjust=False).mean()
    last = main_df.iloc[-1]
    
    # Top Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Price", f"${last['close']:.2f}")
    c2.metric("EMA 9", f"${last['ema9']:.2f}")
    c3.metric("RVOL", f"{(last['volume']/main_df['volume'].mean()):.1f}x")

    # Compact Chart (Reduced Size for iMac Screen)
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(main_df.index, main_df['close'], color='#0066cc', label='Price', linewidth=2)
    ax.plot(main_df.index, main_df['ema9'], color='#28a745', label='EMA 9', linestyle='--')
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    ax.grid(color='#f1f3f5')
    ax.legend(prop={'size': 8})
    ax.tick_params(labelsize=8)
    st.pyplot(fig)

    # Intelligence Feed
    st.subheader("📰 AI Intelligence Feed")
    news_feed = yf.Ticker(selected_ticker).news[:3]
    for n in news_feed:
        with st.expander(f"{n.get('publisher')}: {n.get('title')[:60]}..."):
            st.write(n.get('title'))
            st.caption(f"[Full Article]({n.get('link')})")
else:
    st.error("Engine searching for market connection...")
