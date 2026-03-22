import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- 1. SETTINGS & REFRESH ---
st.set_page_config(layout="wide", page_title="Apex Strategic Command")
st_autorefresh(interval=60 * 1000, key="momentum_sync")

# --- 2. THE ENGINE: DATA & SIGNALING ---
@st.cache_data(ttl=300)
def get_stock_data(ticker):
    try:
        # Pulling 60 days of data for technical analysis
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty: return None
        
        # Technical Calculations
        last_price = df['Close'].iloc[-1]
        ema9 = df['Close'].ewm(span=9, adjust=False).mean()
        last_ema9 = ema9.iloc[-1]
        rvol = df['Volume'].iloc[-1] / df['Volume'].mean()
        
        # Signal Logic
        is_bullish = last_price > last_ema9
        status_color = "#28a745" if is_bullish else "#dc3545" # Green if above EMA, Red if below
        status_text = "STRATEGIC ALIGNMENT: BULLISH" if is_bullish else "STRATEGIC ALIGNMENT: BEARISH"
        
        return {
            "df": df, "price": last_price, "ema9": last_ema9, "ema_series": ema9,
            "rvol": rvol, "color": status_color, "text": status_text
        }
    except Exception as e:
        return None

# --- 3. SIDEBAR: NAVIGATION ---
st.sidebar.title("⚡ Momentum Scan")
watchlist = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
selected_ticker = st.sidebar.selectbox("Select Active Terminal", watchlist)

# --- 4. MAIN INTERFACE ---
data = get_stock_data(selected_ticker)

if data:
    st.header(f"🛡️ {selected_ticker} Strategic Command")
    
    # SIGNAL BANNER
    st.markdown(f"""
        <div style="background-color:{data['color']}; padding:10px; border-radius:5px; text-align:center; color:white; font-weight:bold;">
            ⚠️ {data['text']}
        </div>
    """, unsafe_allow_html=True)
    
    # METRICS ROW
    m1, m2, m3 = st.columns(3)
    m1.metric("Price", f"${data['price']:.2f}")
    m2.metric("EMA 9", f"${data['ema9']:.2f}")
    m3.metric("RVOL", f"{data['rvol']:.2f}x")
    
    # THE TECHNICAL CHART
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(data['df'].index, data['df']['Close'], label="Price Action", color="#0066cc", linewidth=2)
    ax.plot(data['ema_series'].index, data['ema_series'], label="EMA 9", color="#28a745", linestyle="--", alpha=0.7)
    ax.set_facecolor('white')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.3)
    ax.legend()
    st.pyplot(fig)
else:
    st.error("Failed to retrieve market data. Please check your connection.")
