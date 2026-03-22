import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# --- 1. PRO UI ARCHITECTURE ---
st.markdown("""
    <style>
    .sentiment-meter-container {
        background: #111; border: 1px solid #333; padding: 20px;
        border-radius: 10px; text-align: center; margin-bottom: 20px;
    }
    .gauge-text { font-size: 32px; font-weight: 900; }
    .social-feed-container { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 10px; }
    .social-card {
        min-width: 280px; background: #0a0a0a; border: 1px solid #222;
        padding: 15px; border-radius: 8px; border-top: 3px solid #00e5ff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE SOCIAL SENTIMENT ENGINE ---
def get_detailed_sentiment(ticker):
    """Fetches social data and calculates a 0-100% Score"""
    try:
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
        data = requests.get(url, timeout=5).json()
        messages = data.get('messages', [])
        
        bulls = sum(1 for m in messages if m.get('entities', {}).get('sentiment', {}).get('class') == 'bullish')
        bears = sum(1 for m in messages if m.get('entities', {}).get('sentiment', {}).get('class') == 'bearish')
        
        # S-Score Calculation
        total = bulls + bears
        score = (bulls / total * 100) if total > 0 else 50 # Default to Neutral
        return round(score), messages[:5]
    except:
        return 50, []

# --- 3. THE CATALYST & SOCIAL STAGE ---
st.divider()
st.subheader(f"🌪️ {target} CATALYST & SOCIAL HUB")

score, feed = get_detailed_sentiment(target)

# SENTIMENT GAUGE
gauge_col = "#00ff41" if score > 60 else "#ff073a" if score < 40 else "#ffea00"
st.markdown(f"""
    <div class="sentiment-meter-container">
        <span style="color:#888; font-size:12px; text-transform:uppercase;">Crowd Direction</span><br>
        <span class="gauge-text" style="color:{gauge_col};">{score}% BULLISH</span>
        <div style="width:100%; background:#222; height:8px; border-radius:4px; margin-top:10px;">
            <div style="width:{score}%; background:{gauge_col}; height:8px; border-radius:4px; box-shadow: 0 0 10px {gauge_col};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# HORIZONTAL SOCIAL FEED
st.markdown('<div class="social-feed-container">', unsafe_allow_html=True)
cols = st.columns(len(feed)) if feed else [st]
for i, msg in enumerate(feed):
    with cols[i % len(cols)]:
        sentiment = msg.get('entities', {}).get('sentiment', {}).get('class', 'Neutral')
        sent_color = "#00ff41" if sentiment == "bullish" else "#ff073a" if sentiment == "bearish" else "#555"
        st.markdown(f"""
            <div class="social-card">
                <span style="color:{sent_color}; font-weight:bold; font-size:10px;">{sentiment.upper()}</span>
                <p style="font-size:12px; color:#ddd; margin: 8px 0;">{msg['body'][:120]}...</p>
                <span style="color:#444; font-size:10px;">@{msg['user']['username']}</span>
            </div>
            """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
