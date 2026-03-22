import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- 1. CLOUD CONFIG ---
st.set_page_config(layout="wide", page_title="Apex Quant PRO")
st_autorefresh(interval=60 * 1000, key="quant_sync")

# Clean Dark Theme
plt.style.use('dark_background')

# --- 2. DATA ENGINE ---
@st.cache_data(ttl=30)
def get_data(symbol):
    try:
        # Pulling 60 days of daily data for weekend testing
        df = yf.download(symbol, period="60d", interval="1d", progress=False)
        if df.empty: return None
        
        # Standardizing columns
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).lower() for c in df.columns]
        
        # Simple Quant Indicator
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        return df
    except:
        return None

# --- 3. THE TERMINAL ---
st.title("🛡️ Apex Quant AI: Cloud Command")

ticker = st.sidebar.text_input("Enter Ticker ($2-$20 Focus)", value="SOUN").upper()

data = get_data(ticker)

if data is not None:
    last_price = data.iloc[-1]['close']
    st.header(f"{ticker} | Current: ${last_price:.2f}")

    # High-Speed Static Rendering
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(data.index, data['close'], color='#58a6ff', label='Price', linewidth=2)
    ax.plot(data.index, data['ema9'], color='#3fb950', label='EMA 9', linestyle='--')
    
    ax.set_title(f"{ticker} - 60 Day Technical View", color='white')
    ax.spines['bottom'].set_color('#30363d')
    ax.spines['top'].set_color('#30363d') 
    ax.spines['right'].set_color('#30363d')
    ax.spines['left'].set_color('#30363d')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.grid(color='#30363d', linestyle='-', linewidth=0.5)
    ax.legend()

    st.pyplot(fig) # Renders as an image for maximum speed

    # The AI Matrix
    with st.expander("Show AI Raw Data"):
        st.dataframe(data.tail(10), use_container_width=True)
else:
    st.error(f"AI Engine: Searching for {ticker} connection...")
