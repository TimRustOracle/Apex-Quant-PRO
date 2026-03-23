import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & GRID ALIGNMENT CSS ---
st.set_page_config(layout="wide", page_title="APEX ORACLE")
st_autorefresh(interval=30000, key="oracle_pulse")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #fff; font-family: 'Arial', sans-serif; }
    
    /* Create a rigid 4-column grid for headers and rows */
    .oracle-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 2fr 1fr; /* Ticker, Price, Strength Bar, Signal */
        gap: 10px;
        align-items: center;
        padding: 12px;
        border-bottom: 1px solid #222;
    }
    
    .header-row {
        background-color: #0a0a0a;
        color: #00ffcc !important;
        font-weight: bold;
        font-size: 14px;
        text-transform: uppercase;
        border-bottom: 2px solid #333;
    }

    .data-row { font-size: 20px !important; font-weight: 900 !important; }
    .ticker-link { color: #00ffcc; text-decoration: none; }
    
    /* Bar Styling */
    .bar-bg { background: #1a1a1a; border-radius: 4px; width: 100%; max-width: 200px; height: 14px; border: 1px solid #333; }
    .bar-fill { height: 14px; border-radius: 3px; transition: width 0.8s ease-in-out; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE ---
def get_oracle_data(ticker):
    try:
        df = yf.download(ticker, period="1d", interval="5m", progress=False)
        if df is None or df.empty or len(df) < 5: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        price = float(df['Close'].iloc[-1])
        ema = df['Close'].ewm(span=9).mean().iloc[-1]
        
        # Strength Math
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = 100 - (100 / (1 + (gain / loss))) if loss != 0 else 50
        
        score = int(round((rsi * 0.5) + (((price - ema) / ema) * 1500), 0))
        score = min(100, max(5, score))
        
        color = "#FFD700" if score >= 80 else "#00ff00" if score >= 55 else "#ff3333"
        bar_html = f'<div class="bar-bg"><div class="bar-fill" style="width: {score}%; background: {color};"></div></div>'
        
        return {
            "ticker": ticker,
            "price": f"${price:.2f}",
            "bar": bar_html,
            "signal": "🔥 ENTRY" if score >= 60 else "---"
        }
    except: return None

# --- 3. THE DASHBOARD ---
st.title("🔮 APEX ORACLE")

# Header Row
st.markdown("""
    <div class="oracle-grid header-row">
        <div>TICKER</div>
        <div>PRICE</div>
        <div>STRENGTH</div>
        <div>SIGNAL</div>
    </div>
    """, unsafe_allow_html=True)

watchlist = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST"]

for t in watchlist:
    data = get_oracle_data(t)
    if data:
        st.markdown(f"""
            <div class="oracle-grid data-row">
                <div><a href="https://www.tradingview.com/chart/?symbol={data['ticker']}" target="_blank" class="ticker-link">{data['ticker']}</a></div>
                <div>{data['price']}</div>
                <div>{data['bar']}</div>
                <div style="color: {'#00ffcc' if 'ENTRY' in data['signal'] else '#555'};">{data['signal']}</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")
st.caption("🚀 GOLD (80+) | GREEN (55+) | RED (Neutral)")
