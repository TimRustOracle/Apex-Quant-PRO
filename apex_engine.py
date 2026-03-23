import yfinance as yf
import pandas as pd
import time
import os

# --- CONFIG ---
WATCHLIST = ["MARA", "SOUN", "BBAI", "PLTR", "RIOT", "LCID", "NIO"]
EMA_P = 9
RSI_P = 14
TIMEFRAME = "5m"

def run_apex_scan():
    # Clear terminal for a clean "Dashboard" look
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"--- APEX MASTER SUITE: LOCAL LOGIC PORT ---")
    print(f"Time: {time.strftime('%H:%M:%S')} | Interval: {TIMEFRAME}")
    print("-" * 50)

    for ticker in WATCHLIST:
        try:
            # Fetch and clean data
            df = yf.download(ticker, period="1d", interval=TIMEFRAME, progress=False)
            if df.empty: continue
            
            # Fix for the MultiIndex issue seen in your cloud errors
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Manual Indicator Math (No extra libraries needed)
            # EMA Calculation
            df['EMA'] = df['Close'].ewm(span=EMA_P, adjust=False).mean()
            
            # RSI Calculation
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=RSI_P).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=RSI_P).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Logic Check
            last_price = float(df['Close'].iloc[-1])
            last_ema = float(df['EMA'].iloc[-1])
            last_rsi = float(df['RSI'].iloc[-1])

            # Status and Color Logic
            if last_price > last_ema and last_rsi < 70:
                status = "🚀 BULLISH SETUP"
            elif last_price < last_ema and last_rsi > 30:
                status = "📉 BEARISH SETUP"
            else:
                status = "---"

            print(f"{ticker: <6} | Price: ${last_price:.2f} | RSI: {last_rsi:.1f} | {status}")
            
        except Exception as e:
            continue # Silently skip errors to keep the scanner running

# Main Loop
while True:
    run_apex_scan()
    time.sleep(60) # Refreshes every minute
