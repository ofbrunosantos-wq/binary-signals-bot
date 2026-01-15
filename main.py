import requests
import pandas as pd
import ta
from datetime import datetime, timedelta
import pytz
import os
import time

API_PRICE_KEY = os.getenv("API_PRICE_KEY")
LOVABLE_ENDPOINT = os.getenv("LOVABLE_ENDPOINT")
SECRET_TOKEN = os.getenv("SECRET_TOKEN")

ASSETS = ["EUR/USD", "GBP/USD"]
TIMEFRAME = "5min"
EXPIRATION_MINUTES = 5
TIMEZONE = "America/Sao_Paulo"

def fetch_data(symbol):
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": TIMEFRAME,
        "apikey": API_PRICE_KEY,
        "outputsize": 100
    }
    response = requests.get(url).json()
    df = pd.DataFrame(response["values"])
    df["close"] = df["close"].astype(float)
    return df[::-1]

def calculate_indicators(df):
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
    df["ema9"] = ta.trend.EMAIndicator(df["close"], window=9).ema_indicator()
    df["ema21"] = ta.trend.EMAIndicator(df["close"], window=21).ema_indicator()
    return df

def should_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    if last["rsi"] < 30 and prev["ema9"] < prev["ema21"] and last["ema9"] > last["ema21"]:
        return "CALL"

    if last["rsi"] > 70 and prev["ema9"] > prev["ema21"] and last["ema9"] < last["ema21"]:
        return "PUT"

    return None

def send_signal(signal):
    headers = {
        "Authorization": f"Bearer {SECRET_TOKEN}",
        "Content-Type": "application/json"
    }
    requests.post(LOVABLE_ENDPOINT, json=signal, headers=headers)

def run():
    tz = pytz.timezone(TIMEZONE)

    while True:
        now = datetime.now(tz)

        for asset in ASSETS:
            try:
                df = fetch_data(asset)
                df = calculate_indicators(df)
                direction = should_signal(df)

                if direction:
                    entry_time = now + timedelta(minutes=5)
                    alert_time = entry_time - timedelta(minutes=5)

                    signal = {
                        "asset": asset,
                        "direction": direction,
                        "timeframe": TIMEFRAME,
                        "entry_time": entry_time.isoformat(),
                        "alert_time": alert_time.isoformat(),
                        "expiration_minutes": EXPIRATION_MINUTES,
                        "strategy": "RSI + EMA"
                    }

                    send_signal(signal)
                    print(f"SINAL ENVIADO: {asset} {direction}")

            except Exception as e:
                print("Erro:", e)

        time.sleep(60)

if __name__ == "__main__":
    run()
