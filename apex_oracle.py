import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. CLOUD-OPTIMIZED UI ---
st.set_page_config(layout="wide", page_title="Apex Quant AI", initial_sidebar_state="collapsed")

# Injecting Clean, High-Speed CSS
st.markdown("""
    <style>
    .stApp { background-color: #05070a; color: #ffffff; }
    .quant-card { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 10px; }
    .momentum-bar { height: 12px; background: #161b22; border-radius: 6px; overflow: hidden; margin-top: 5px; }
    .bar-fill { height: 100%; transition: width 0.8s ease; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. QUANTITATIVE AI LOGIC ---
@st.cache_data(ttl=60) # Cloud Caching for Speed
def quant_ai_engine(symbol):
    try:
        # Fetching 2-day high-res data
        df = yf.download(symbol, period="2d", interval="1m", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).lower() for c in df.columns]

        # Quantitative Alpha Factors
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
        df['rvol'] = df['volume'] / df['volume'].rolling(30).mean()
        
        # Opening Range Calculation
        today = df.index[-1].date()
        today_df = df[df.index.date == today]
        or_high = today_df.iloc[:15]['high'].max() if len(today_df) >= 15 else 0
        
        # Quant AI Scoring Algorithm
        last = df.iloc[-1]
        score = 0
        score += 30 if last['close'] > last['ema9'] else 0
        score += 30 if last['close'] > last['vwap'] else 0
        score += 40 if last['rvol'] > 2.0 else 0
        
        return df, score, last['close'], last['rvol'], or_high
    except: return None

# --- 3. THE COMMAND CENTER ---
st.title("🛡️ Apex Quant AI: Cloud Command")

watch_list = ["SOUN", "BBAI", "PLTR", "MARA", "RIOT", "LCID", "NIO"]

# Sidebar-style Scanner to maximize chart space
with st.sidebar:
    st.header("⚡ Live Scanner")
    ranked_data = []
    for s in watch_list:
        res = quant_ai_engine(s)
        if res: ranked_data.append({"ticker": s, "score": res[1], "price": res[2]})
    
    df_ranked = pd.DataFrame(ranked_data).sort_values("score", ascending=False)
    
    for row in df_ranked.itertuples():
        if st.button(f"{row.ticker} | {row.score}%", key=f"btn_{row.ticker}"):
            st.session_state.active_ticker = row.ticker
        color = "#3fb950" if row.score > 60 else "#f85149"
        st.markdown(f'<div class="momentum-bar"><div class="bar-fill" style="width:{row.score}%; background:{color};"></div></div>', unsafe_allow_html=True)

# --- 4. THE PRO CHART ---
active = st.session_state.get('active_ticker', "SOUN")
bundle = quant_ai_engine(active)

if bundle:
    df, score, price, rvol, or_h = bundle
    st.write(f"### Monitoring: **{active}** | Price: **${price:.2f}** | RVOL: **{rvol:.1f}x**")
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.85, 0.15])
    
    # OR High Line
    if or_h > 0:
        fig.add_hline(y=or_h, line_dash="dash", line_color="#58a6ff", annotation_text="OR High")
    
    # Candlestick + Indicators
    fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close']), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['vwap'], name="VWAP", line=dict(color='yellow', width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['ema9'], name="EMA 9", line=dict(color='green', width=1.5)), row=1, col=1)
    
    # Volume
    colors = ['#00d4ff' if v > 2.5 else '#2ea043' for v in df['rvol']]
    fig.add_trace(go.Bar(x=df.index, y=df['volume'], marker_color=colors), row=2, col=1)
    
    fig.update_layout(height=700, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=0, r=40, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})