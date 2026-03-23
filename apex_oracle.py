import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & SLIM STYLING ---
st.set_page_config(layout="wide", page_title="APEX ORACLE")
st_autorefresh(interval=30000, key="oracle_pulse")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    /* Slim down the table and rows */
    .stTable td { padding: 5px !important; font-size: 18px !important; font-weight: bold; }
    /* Progress Bar Container */
    .progress-bg { background-color: #222; border-radius: 5px; width: 100%; height: 20px; }
    .progress-fill { height: 20px; border-radius: 5px; transition: width 0.5s ease-in-out; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE ---
def get_oracle_data(ticker):
    try:
        df = yf.download(ticker, period="1d", interval="5m", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        price = df['Close'].iloc[-1]
        ema = df['Close'].ewm(span=9).mean().iloc[-1]
        rsi_val = 14
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_val).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_val).mean().iloc[-1]
        rsi = 100 - (100 / (1 + (gain / loss)))
        
        # Strength Score (0-100)
        score = (rsi * 0.6) + (((price - ema) / ema) * 1000)
        score = int(round(min(100, max(0, score)), 0))
        
        # COLOR LOGIC: Red -> Green -> Gold
        if score >= 85: color = "#FFD700" # GOLD
        elif score >= 60: color = "#00FF00" # GREEN
        else: color = "#FF0000" # RED

        # Custom Sliding Bar HTML
        bar_html = f'''
            <div class="progress-bg">
                <div class="progress-fill" style="width: {score}%; background-color: {color};"></div>
            </div>
        '''

        return {
            "TICKER": ticker,
            "PRICE": f"${price:.2f}",
            "STRENGTH": bar_html,
            "SCORE": score,
            "SIGNAL": "🔥 BUY" if score >= 60 else "---"
        }
    except: return None

# --- 3. THE DASHBOARD ---
st.title("🔮 APEX ORACLE")

watchlist = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "GNS", "HOLO", "UPST", "TPST"]
data_list = [get_oracle_data(t) for t in watchlist if get_oracle_data(t) is not None]
df = pd.DataFrame(data_list)

if not df.empty:
    # Use st.write with unsafe_allow_html to render the sliding bars
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

st.divider()
st.info("💡 GOLD (85+) = Extreme Momentum | GREEN (60+) = Apex Entry | RED = No Trade")
