import streamlit as st
import requests
import time

# --- 1. CONFIG ---
st.set_page_config(layout="wide", page_title="APEX REAL-TIME")

FINNHUB_KEY = "d70n0i9r01ql6rnvssl0d70n0i9r01ql6rnvsslg"

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #fff; }
    .oracle-grid { display: grid; grid-template-columns: 100px 90px 90px 100px 1fr; gap: 12px; align-items: center; padding: 10px; border-bottom: 1px solid #222; }
    .header-row { color: #00ffcc; font-weight: bold; text-transform: uppercase; border-bottom: 2px solid #333; }
    .tv-link { color: #00ffcc !important; text-decoration: none; border: 1px solid #00ffcc; padding: 2px 8px; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LIVE DASHBOARD SPACE ---
st.title("🔮 APEX ORACLE: SILENT STREAM")
# This "empty" container is the secret to no-refresh updates
dashboard = st.empty()

watchlist = ["AEMD", "TPET", "MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO", "WULF", "LUNR", "OKLO", "NNE"]

# --- 3. THE LIVE LOOP ---
while True:
    with dashboard.container():
        st.markdown('<div class="oracle-grid header-row"><div>Ticker</div><div>Price</div><div>Change</div><div>Strength</div><div>Signal</div></div>', unsafe_allow_html=True)
        
        for ticker in watchlist:
            try:
                # Instant Price Pulse
                res = requests.get(f'https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_KEY}').json()
                price = res.get('c', 0)
                change = res.get('dp', 0)
                
                # Visual Logic
                color = "#00ff00" if change >= 0 else "#ff3333"
                bar_width = int(min(100, max(10, 50 + (change * 5))))
                tv_url = f"https://www.tradingview.com/chart/?symbol={ticker}"

                st.markdown(f"""
                    <div class="oracle-grid">
                        <div><a href="{tv_url}" target="_blank" class="tv-link">{ticker}</a></div>
                        <div style="font-weight:bold;">${price:.2f}</div>
                        <div style="color:{color};">{change:.2f}%</div>
                        <div style="background:#111; height:8px;"><div style="width:{bar_width}%; background:#00ffcc; height:8px;"></div></div>
                        <div style="font-size:11px; color:#555;">STREAMING...</div>
                    </div>
                """, unsafe_allow_html=True)
            except:
                continue
    
    # ADJUST THIS: 1.0 for stability, 0.5 for hyper-speed
    time.sleep(1)
