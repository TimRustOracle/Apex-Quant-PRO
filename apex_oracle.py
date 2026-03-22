import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# --- 1. INITIALIZE AI BRAIN ---
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()

# --- 2. PRO THEME ---
st.set_page_config(layout="wide", page_title="Apex Quant AI", page_icon="🛡️")
st_autorefresh(interval=60 * 1000, key="terminal_sync")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1d23; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; }
    .sentiment-box { padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #dee2e6; }
    h1, h2, h3 { color: #004a99 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA & SENTIMENT ENGINE ---
def get_sentiment_score(news_list):
    if not news_list: return 0
    scores = [sia.polarity_scores(item['title'])['compound'] for item in news_list]
    return sum(scores) / len(scores)

@st.cache_data(ttl=300)
def run_scanner():
    watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
    results = []
    for t in watchlist:
        try:
            tk = yf.Ticker(t)
            price = tk.history(period="1d")['Close'].iloc[-1]
            if 2.0 <= price <= 20.0:
                results.append({'Ticker': t, 'Price': price})
        except: continue
    return pd.DataFrame(results)

# --- 4. SIDEBAR: SCANNER & AI SENTIMENT ---
with st.sidebar:
    st.header("🔍 Market Scan")
    scan_df = run_scanner()
    active_ticker = st.selectbox("Active Terminal", scan_df['Ticker'].tolist()) if not scan_df.empty else "SOUN"
    
    st.divider()
    st.subheader("🧠 AI Sentiment Analysis")
    
    ticker_obj = yf.Ticker(active_ticker)
    news = ticker_obj.news[:8]
    score = get_sentiment_score(news)
    
    # Sentiment Visual
    color = "#28a745" if score > 0.05 else "#dc3545" if score < -0.05 else "#6c757d"
    st.markdown(f"""
        <div style="background:{color}; color:white; padding:20px; border-radius:10px; text-align:center;">
            <h2 style="color:white !important; margin:0;">{score:+.2f}</h2>
            <p style="margin:0;">Institutional Sentiment</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    for item in news:
        sent = sia.polarity_scores(item['title'])['compound']
        icon = "✅" if sent > 0 else "❌" if sent < 0 else "⚪"
        st.markdown(f"{icon} **{item['title']}**")
        st.caption(f"[{item['publisher']}]({item['link']})")

# --- 5. MAIN TERMINAL ---
@st.cache_data(ttl=60)
def get_main_data(symbol):
    df = yf.download(symbol, period="60d", interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    return df

st.title(f"📊 {active_ticker} Strategic Terminal")
data = get_main_data(active_ticker)

if data is not None:
    # Price Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Current Price", f"${data['close'].iloc[-1]:.2f}")
    c2.metric("9-Day EMA", f"${data['ema9'].iloc[-1]:.2f}")
    c3.metric("AI Bias", "BULLISH" if score > 0 else "BEARISH")

    # The Master Suite Chart
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(data.index, data['close'], color='#0066cc', label='Price Action', linewidth=2.5)
    ax.plot(data.index, data['ema9'], color='#28a745', label='EMA 9 (Trend)', linestyle='--')
    
    ax.set_facecolor('#ffffff')
    fig.patch.set_facecolor('#ffffff')
    ax.grid(color='#f1f3f5', linestyle='-', linewidth=0.5)
    ax.legend()
    st.pyplot(fig)
