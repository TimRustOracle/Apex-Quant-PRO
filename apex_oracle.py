import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide", page_title="Apex Quant PRO")
st_autorefresh(interval=60 * 1000, key="quant_sync")
plt.style.use('dark_background')

@st.cache_data(ttl=30)
def get_data(symbol):
    try:
        df = yf.download(symbol, period="60d", interval="1d", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).lower() for c in df.columns]
        
        # Quantitative Calculations
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['vol_avg'] = df['volume'].rolling(20).mean()
        df['rvol'] = df['volume'] / df['vol_avg']
        return df
    except:
        return None

st.title("🛡️ Apex Quant AI: Pro Command")

ticker = st.sidebar.text_input("Enter Ticker", value="SOUN").upper()
data = get_data(ticker)

if data is not None:
    last = data.iloc[-1]
    
    # AI Scoreboard
    c1, c2, c3 = st.columns(3)
    c1.metric("Current Price", f"${last['close']:.2f}")
    c2.metric("Relative Volume (RVOL)", f"{last['rvol']:.2f}x")
    c3.metric("Trend", "BULLISH" if last['close'] > last['ema9'] else "BEARISH")

    # Dual-Panel Charting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
    
    # Panel 1: Price Action
    ax1.plot(data.index, data['close'], color='#58a6ff', label='Price', linewidth=2)
    ax1.plot(data.index, data['ema9'], color='#3fb950', label='EMA 9', linestyle='--')
    ax1.set_title(f"{ticker} Institutional Matrix", color='white', loc='left')
    
    # Panel 2: RVOL Heatmap
    colors = ['#238636' if r > 2 else '#30363d' for r in data['rvol']]
    ax2.bar(data.index, data['volume'], color=colors, alpha=0.8)
    ax2.set_ylabel("Volume", color='white')

    # Formatting
    for ax in [ax1, ax2]:
        ax.tick_params(colors='white')
        ax.grid(color='#30363d', linestyle='-', linewidth=0.5)
        for spine in ax.spines.values(): spine.set_color('#30363d')

    st.pyplot(fig)
else:
    st.error("Connecting to Data Stream...")
