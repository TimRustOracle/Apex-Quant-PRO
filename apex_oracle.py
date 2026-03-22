import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- 1. THE "CLEAN WHITE" THEME ENGINE ---
st.set_page_config(layout="wide", page_title="Apex Quant PRO", page_icon="📈")
st_autorefresh(interval=60 * 1000, key="premarket_sync")

# Force everything to the "Stocks to Trade" white professional look
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1d23; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; }
    .stMetric { background-color: #ffffff; border: 1px solid #dee2e6; padding: 15px; border-radius: 10px; }
    h1, h2, h3, p { color: #1a1d23 !important; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PRE-MARKET SCANNER LOGIC ($2-$20 FOCUS) ---
@st.cache_data(ttl=300)
def run_premarket_scan():
    # Focused watchlist of high-momentum small/mid caps
    tickers = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO", "GNS", "HOLO", "TPST"]
    scan_results = []
    
    for t in tickers:
        try:
            df = yf.download(t, period="2d", interval="1m", progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                df.columns = [str(c).lower() for c in df.columns]
                
                price = df.iloc[-1]['close']
                # Pre-market logic: Only include if in your $2-$20 sweet spot
                if 2.0 <= price <= 20.0:
                    change = ((price - df.iloc[0]['close']) / df.iloc[0]['close']) * 100
                    scan_results.append({'Ticker': t, 'Price': price, '% Change': change})
        except: continue
    return pd.DataFrame(scan_results).sort_values('% Change', ascending=False)

# --- 3. SIDEBAR: THE TOP 10-20 SCANNER ---
with st.sidebar:
    st.header("🔍 Pre-Market Scan")
    st.write("Target: $2 - $20 Small Caps")
    
    scan_data = run_premarket_scan()
    if not scan_data.empty:
        # Display the Top Picks as clickable buttons or a table
        st.dataframe(scan_data.style.format({'Price': '{:.2f}', '% Change': '{:+.2f}%'}), 
                     hide_index=True, use_container_width=True)
        
        selected_ticker = st.selectbox("Select Active Terminal", scan_data['Ticker'].tolist())
    else:
        selected_ticker = st.text_input("Manual Ticker Entry", value="SOUN").upper()

# --- 4. MAIN TERMINAL: QUANTITATIVE ANALYSIS ---
@st.cache_data(ttl=60)
def get_terminal_data(symbol):
    df = yf.download(symbol, period="60d", interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['vol_avg'] = df['volume'].rolling(20).mean()
    df['rvol'] = df['volume'] / df['vol_avg']
    return df

st.title(f"📊 {selected_ticker} Command Terminal")
data = get_terminal_data(selected_ticker)

if data is not None:
    last = data.iloc[-1]
    
    # Pro Scoreboard
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Price", f"${last['close']:.2f}")
    c2.metric("RVOL (Relative Vol)", f"{last['rvol']:.2f}x")
    c3.metric("9-Day EMA", f"${last['ema9']:.2f}")
    c4.metric("Status", "STRENGTH" if last['close'] > last['ema9'] else "WEAKNESS")

    # The Chart (Clean White Style)
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(data.index, data['close'], color='#0066cc', label='Price Action', linewidth=2.5)
    ax.plot(data.index, data['ema9'], color='#28a745', label='Institutional EMA 9', linestyle='--')
    
    # Visual Formatting for "Stocks to Trade" Look
    ax.set_facecolor('#ffffff')
    fig.patch.set_facecolor('#ffffff')
    ax.spines['bottom'].set_color('#dee2e6')
    ax.spines['left'].set_color('#dee2e6')
    ax.grid(color='#f1f3f5', linestyle='-', linewidth=0.5)
    ax.tick_params(colors='#495057')
    ax.legend(facecolor='white', edgecolor='#dee2e6', labelcolor='black')
    
    st.pyplot(fig)
