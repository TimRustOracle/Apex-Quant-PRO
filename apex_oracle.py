import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# --- 1. SETUP & THEME ---
try:
    nltk.data.find('vader_lexicon')
except:
    nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()
st.set_page_config(layout="wide", page_title="Apex Golden Terminal")
st_autorefresh(interval=60 * 1000, key="momentum_sync")

# Professional Clean White Styling
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; min-width: 350px; }
    .momentum-bar { height: 20px; border-radius: 10px; margin-top: 5px; margin-bottom: 15px; border: 1px solid #ddd; }
    .gold-glow { box-shadow: 0 0 10px #ffd700; border: 2px solid #ffd700 !important; }
    h1, h2, h3 { color: #004a99 !important; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOMENTUM ENGINE ---
def get_momentum_score(ticker):
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period="5d", interval="1d")
        if df.empty: return 0, "Red"
        
        # Technicals
        price = df.iloc[-1]['Close']
        ema9 = df['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
        vol_avg = df['Volume'].mean()
        rvol = df.iloc[-1]['Volume'] / vol_avg
        
        # Sentiment
        news = tk.news[:5]
        s_score = sum([sia.polarity_scores(n.get('title', ''))['compound'] for n in news]) / 5 if news else 0
        
        # Scoring Logic
        score = 0
        if price > ema9: score += 40
        if rvol > 1.5: score += 30
        if s_score > 0.1: score += 30
        
        color = "#dc3545" # Red
        if 40 <= score < 80: color = "#28a745" # Green
        if score >= 90: color = "#ffd700" # Gold
        
        return score, color
    except:
        return 0, "#dc3545"

# --- 3. SIDEBAR: MOMENTUM BARS ---
with st.sidebar:
    st.header("⚡ Momentum Scan")
    st.caption("$2 - $20 High-Velocity Targets")
    
    watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
    selected_ticker = st.radio("Select Active Terminal", watchlist, horizontal=False)
    
    st.divider()
    for t in watchlist:
        m_score, m_color = get_momentum_score(t)
        is_gold = "gold-glow" if m_color == "#ffd700" else ""
        st.markdown(f"**{t}**")
        st.markdown(f"""
            <div class="momentum-bar {is_gold}" style="background: linear-gradient(90deg, {m_color} {m_score}%, #eee {m_score}%);"></div>
        """, unsafe_allow_html=True)

# --- 4. MAIN TERMINAL: COMPACT VIEW ---
st.title(f"🛡️ {selected_ticker} Command")

df = yf.download(selected_ticker, period="60d", interval="1d", progress=False)
df.columns = [str(c).lower() for c in df.columns]
df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()

# Metrics Row
c1, c2, c3, c4 = st.columns(4)
last = df.iloc[-1]
c1.metric("Price", f"${last['close']:.2f}")
c2.metric("EMA 9", f"${last['ema9']:.2f}")
c3.metric("RVOL", f"{(last['volume']/df['volume'].mean()):.1f}x")
c4.write("### ✅ PRO SIGNAL" if last['close'] > last['ema9'] else "### ⏳ MONITORING")

# COMPACT CHART (Reduced Size)
fig, ax = plt.subplots(figsize=(10, 3)) # Shorter height
ax.plot(df.index, df['close'], color='#0066cc', linewidth=2, label="Price")
ax.plot(df.index, df['ema9'], color='#28a745', linestyle='--', label="EMA 9")
ax.set_facecolor('white')
fig.patch.set_facecolor('white')
ax.grid(color='#f1f3f5')
ax.tick_params(axis='both', which='major', labelsize=8)
st.pyplot(fig)

# News & Log below
st.divider()
col_left, col_right = st.columns(2)
with col_left:
    st.subheader("📰 Intelligence")
    for n in yf.Ticker(selected_ticker).news[:3]:
        st.caption(f"**{n.get('title')}**")
with col_right:
    st.subheader("🖋️ Trade Log")
    note = st.text_input("Quick Note")
    if st.button("Save Log"):
        st.success("Noted.")
