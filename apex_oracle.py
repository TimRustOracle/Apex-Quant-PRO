import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# --- 1. SETUP ---
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()
st.set_page_config(layout="wide", page_title="Apex Quant PRO", page_icon="🛡️")
st_autorefresh(interval=60 * 1000, key="terminal_heartbeat")

# Clean White Theme
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1d23; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; }
    .signal-card { padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE SENTIMENT ENGINE (Fixed KeyError) ---
def analyze_market_mind(ticker_obj):
    try:
        news_data = ticker_obj.news
        if not news_data: return 0, []
        processed_news = []
        scores = []
        for item in news_data:
            # Flexible key checking for 'title' or 'headline'
            title = item.get('title') or item.get('headline') or "No Title"
            s_score = sia.polarity_scores(title)['compound']
            scores.append(s_score)
            processed_news.append({'title': title, 'score': s_score, 'link': item.get('link', '#')})
        avg_score = sum(scores) / len(scores)
        return avg_score, processed_news
    except: return 0, []

# --- 3. THE SCANNER ---
@st.cache_data(ttl=300)
def run_scan():
    watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
    results = []
    for t in watchlist:
        try:
            p = yf.Ticker(t).history(period="1d")['Close'].iloc[-1]
            if 2.0 <= p <= 20.0: results.append(t)
        except: continue
    return results

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("🔍 Pre-Market Scan")
    tickers = run_scan()
    active_ticker = st.selectbox("Switch Terminal", tickers if tickers else ["SOUN"])
    
    st.divider()
    st.subheader("🧠 Institutional Mood")
    tk_obj = yf.Ticker(active_ticker)
    mood_score, news_items = analyze_market_mind(tk_obj)
    
    mood_color = "#28a745" if mood_score > 0.1 else "#dc3545" if mood_score < -0.1 else "#6c757d"
    st.markdown(f'<div style="background:{mood_color}; color:white; padding:15px; border-radius:8px; text-align:center;">'
                f'<h2 style="color:white !important; margin:0;">{mood_score:+.2f}</h2>Score</div>', unsafe_allow_html=True)
    
    for n in news_items[:5]:
        icon = "🟢" if n['score'] > 0 else "🔴" if n['score'] < 0 else "⚪"
        st.markdown(f"{icon} [{n['title']}]({n['link']})")

# --- 5. MAIN TERMINAL ---
df = yf.download(active_ticker, period="60d", interval="1d", progress=False)
if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
df.columns = [str(c).lower() for c in df.columns]
df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
df['vol_avg'] = df['volume'].rolling(20).mean()
df['rvol'] = df['volume'] / df['vol_avg']

last = df.iloc[-1]
st.title(f"🛡️ {active_ticker} Strategic Command")

# THE SIGNAL ENGINE
is_bullish = (last['close'] > last['ema9']) and (mood_score > 0.05)
is_bearish = (last['close'] < last['ema9']) and (mood_score < -0.05)

if is_bullish:
    st.markdown('<div class="signal-card" style="background:#28a745;">🚀 STRATEGIC ALIGNMENT: BULLISH SIGNAL</div>', unsafe_allow_html=True)
elif is_bearish:
    st.markdown('<div class="signal-card" style="background:#dc3545;">⚠️ STRATEGIC ALIGNMENT: BEARISH SIGNAL</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="signal-card" style="background:#6c757d;">⚖️ MONITORING: NO CLEAR ALIGNMENT</div>', unsafe_allow_html=True)

# Main Stats
c1, c2, c3 = st.columns(3)
c1.metric("Price", f"${last['close']:.2f}")
c2.metric("RVOL", f"{last['rvol']:.2f}x")
c3.metric("EMA 9 Gap", f"${(last['close'] - last['ema9']):.2f}")

# Chart
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df.index, df['close'], color='#0066cc', label='Price Action', linewidth=2)
ax.plot(df.index, df['ema9'], color='#28a745', label='EMA 9', linestyle='--')
ax.set_facecolor('white')
fig.patch.set_facecolor('white')
ax.grid(color='#f1f3f5')
ax.legend()
st.pyplot(fig)
