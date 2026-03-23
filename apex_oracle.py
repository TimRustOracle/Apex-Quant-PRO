import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & PRO-STYLING ---
st.set_page_config(layout="wide", page_title="APEX ORACLE")
st_autorefresh(interval=60000, key="oracle_pulse")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #fff; font-family: 'Arial', sans-serif; }
    .oracle-grid { display: grid; grid-template-columns: 120px 100px 100px 1fr 100px; gap: 15px; align-items: center; padding: 10px; border-bottom: 1px solid #222; }
    .header-row { background-color: #111; color: #00ffcc !important; font-weight: bold; font-size: 13px; text-transform: uppercase; border-bottom: 2px solid #333; position: sticky; top: 0; z-index: 99; }
    .data-row { font-size: 20px !important; font-weight: 900 !important; }
    .bar-bg { background: #1a1a1a; border-radius: 4px; width: 100%; height: 16px; border: 1px solid #333; }
    .bar-fill { height: 16px; border-radius: 3px; transition: width 0.8s ease-in-out; }
    .news-card { background: #0a0a0a; padding: 12px; border-left: 4px solid #00ffcc; margin-bottom: 8px; border-radius: 4px; font-size: 14px; }
    .bullish { color: #00ff00; font-weight: bold; }
    .bearish { color: #ff3333; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE ---
def get_oracle_data(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="5d", interval="5m")
        if df.empty or len(df) < 20: return None
        
        # Current Stats
        price = float(df['Close'].iloc[-1])
        curr_vol = df['Volume'].iloc[-1]
        avg_vol = df['Volume'].mean()
        vol_mult = round(curr_vol / avg_vol, 1) if avg_vol > 0 else 1.0

        # Day Trading Filter ($2 - $20)
        if not (2.0 <= price <= 20.0): return None

        # EMA & RSI Logic
        ema = df['Close'].ewm(span=9).mean().iloc[-1]
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = 100 - (100 / (1 + (gain / loss))) if loss != 0 else 50
        
        # Apex Score
        score = int(round((rsi * 0.4) + (((price - ema) / ema) * 1500) + (vol_mult * 5), 0))
        score = min(100, max(5, score))
        
        color = "#FFD700" if score >= 80 else "#00ff00" if score >= 55 else "#ff3333"
        bar_html = f'<div class="bar-bg"><div class="bar-fill" style="width: {score}%; background: {color};"></div></div>'
        
        # Sentiment Helper
        news_list = []
        if t.news:
            for n in t.news[:2]:
                title = n.get('title', '').upper()
                sent = "[NEUTRAL]"
                if any(w in title for w in ["UPGRADE", "BEAT", "PARTNERSHIP", "BREAKOUT", "BULLISH", "BUY"]): sent = "[BULLISH]"
                if any(w in title for w in ["DOWNGRADE", "MISS", "LAWSUIT", "DEBT", "BEARISH", "SELL"]): sent = "[BEARISH]"
                news_list.append({'pub': n.get('publisher', 'Market'), 'title': n.get('title', ''), 'sent': sent})

        return {
            "ticker": ticker, "price": f"${price:.2f}", "vol_mult": f"{vol_mult}x",
            "bar": bar_html, "score": score, "news": news_list
        }
    except: return None

# --- 3. THE DASHBOARD ---
st.title("🔮 APEX ORACLE: COMMAND CENTER")

scan_pool = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST", "TPET", "BTBT", "MSTR", "CAN", "WULF", "CLEU", "BXRX", "AEMD", "SERV", "LUNR", "OKLO", "NNE", "SISI", "ZAPP", "AEI", "KULR", "TTOO", "FFIE", "GWAV"]

all_data = []
for ticker in scan_pool:
    res = get_oracle_data(ticker)
    if res: all_data.append(res)

top_20 = sorted(all_data, key=lambda x: x['score'], reverse=True)[:20]

# UI Header
st.markdown('<div class="oracle-grid header-row"><div>TICKER</div><div>PRICE</div><div>VOL X</div><div>STRENGTH</div><div>SIGNAL</div></div>', unsafe_allow_html=True)

final_catalysts = []
for d in top_20:
    signal = "🔥 GOLD" if d['score'] >= 80 else "⚡ ACTIVE"
    st.markdown(f"""
        <div class="oracle-grid data-row">
            <div><a href="https://www.tradingview.com/chart/?symbol={d['ticker']}" target="_blank" style="color:#00ffcc; text-decoration:none;">{d['ticker']}</a></div>
            <div>{d['price']}</div>
            <div style="color: {'#00ff00' if float(d['vol_mult'][:-1]) > 1.5 else '#555'};">{d['vol_mult']}</div>
            <div>{d['bar']}</div>
            <div style="font-size:14px; color:{'#FFD700' if 'GOLD' in signal else '#555'};">{signal}</div>
        </div>
        """, unsafe_allow_html=True)
    final_catalysts.extend(d['news'])

# News Section
st.markdown("<br><br><h3>📰 LIVE CATALYST & SENTIMENT</h3>", unsafe_allow_html=True)
if final_catalysts:
    seen = set()
    for n in final_catalysts:
        if n['title'] not in seen:
            s_class = "bullish" if n['sent'] == "[BULLISH]" else "bearish" if n['sent'] == "[BEARISH]" else ""
            st.markdown(f'<div class="news-card"><span class="{s_class}">{n["sent"]}</span> | <b>{n["pub"]}</b>: {n["title"]}</div>', unsafe_allow_html=True)
            seen.add(n['title'])
