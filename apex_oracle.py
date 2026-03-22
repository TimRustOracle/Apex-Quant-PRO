import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- 1. SETTINGS ---
st.set_page_config(layout="wide", page_title="Apex Quant PRO")
st_autorefresh(interval=60 * 1000, key="quant_sync")

# --- 2. ENGINE ---
@st.cache_data(ttl=30)
def get_data(symbol):
    try:
        # Using 60 days of daily data for a guaranteed visual "Win" while market is closed
        df = yf.download(symbol, period="60d", interval="1d", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).lower() for c in df.columns]
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        return df
    except: return None

# --- 3. UI ---
st.title("🛡️ Apex Quant AI: High-Speed Terminal")

ticker = st.sidebar.text_input("Ticker", value="SOUN").upper()

data = get_data(ticker)

if data is not None:
    # Metric Bar
    last_price = data.iloc[-1]['close']
    st.metric(f"Current {ticker} Price", f"${last_price:.2f}")

    # "Light" Charting (Faster for older Macs)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(data.index, data['close'], color='#58a6ff', label='Price')
    ax.plot(data.index, data['ema9'], color='#3fb950', label='EMA 9')
    ax.set_facecolor('#05070a')
    fig.patch.set_facecolor('#05070a')
    ax.tick_params(colors='white')
    ax.legend()
    st.pyplot(fig) # This renders as a simple image, much faster than Plotly

    # Debug Table (Proof the AI is working)
    with st.expander("View Raw AI Matrix"):
        st.table(data.tail(5))
else:
    st.error("Searching for Data Stream...")
