# ============================================================
#  GOD'S EYE – GOLD ORACLE v1.0
#  Leak-free | Flood-safe | Single-user | Trader-grade
# ============================================================

import os
import time
import requests
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from sklearn.ensemble import GradientBoostingClassifier

# -----------------------------
# TELEGRAM CONFIG
# -----------------------------
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise SystemExit("TG_TOKEN ve TG_CHAT ortam değişkenleri ayarlanmalı.")

CHAT_ID = int(CHAT_ID)

# -----------------------------
# DATA LOADER (Aligned & Clean)
# -----------------------------
def load_data():
    ons = yf.download("GC=F", period="5y", auto_adjust=True, progress=False)
    usd = yf.download("USDTRY=X", period="5y", auto_adjust=True, progress=False)
    dxy = yf.download("DX-Y.NYB", period="5y", auto_adjust=True, progress=False)

    df = pd.concat([
        ons['Close'].rename("ONS"),
        usd['Close'].rename("USD"),
        dxy['Close'].rename("DXY")
    ], axis=1)

    df['RSI'] = ta.rsi(df['ONS'], length=14)

    adx = ta.adx(ons['High'], ons['Low'], ons['Close'])
    df['ADX'] = adx['ADX_14']

    return df.dropna()

# -----------------------------
# MODEL TRAIN (NO DATA LEAK)
# -----------------------------
def train_model(df):
    df = df.copy()
    df['FUTURE'] = df['ONS'].shift(-10)
    df['UP'] = (df['FUTURE'] > df['ONS']).astype(int)

    features = ['ONS', 'RSI', 'ADX', 'DXY']
    train = df.dropna()

    model = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=3,
        random_state=42
    )

    model.fit(train[features], train['UP'])
    return model

# -----------------------------
# TODAY ANALYSIS
# -----------------------------
def analyze_today(df, model):
    last = df.iloc[-1]

    prob = model.predict_proba([[
        float(last['ONS']),
        float(last['RSI']),
        float(last['ADX']),
        float(last['DXY'])
    ]])[0][1]

    gram = (float(last['ONS']) / 31.1035) * float(last['USD'])

    return {
        "gram": gram,
        "ons": float(last['ONS']),
        "adx": float(last['ADX']),
        "rsi": float(last['RSI']),
        "prob": float(prob)
    }

# -----------------------------
# TELEGRAM SEND
# -----------------------------
def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": msg
    }, timeout=5)

# -----------------------------
# REPORT
# -----------------------------
def build_report(r):
    if r['prob'] > 0.6:
        yön = "⬆️ YÜKSELİŞ"
    elif r['prob'] < 0.4:
        yön = "⬇️ BASKI"
    else:
        yön = "➡️ KARARSIZ"

    return (
        "🧠 GOD'S EYE – ALTIN RADARI\n\n"
        f"💰 Gram: {r['gram']:.2f} TL\n"
        f"🌍 Ons: {r['ons']:.2f} $\n\n"
        f"📊 RSI: {r['rsi']:.1f}\n"
        f"💪 ADX: {r['adx']:.1f}\n\n"
        f"🔮 Yükseliş Olasılığı: %{r['prob']*100:.1f}\n"
        f"📡 Piyasa Yönü: {yön}"
    )

# -----------------------------
# TELEGRAM LISTENER (LONG POLL)
# -----------------------------
last_update = 0

def poll():
    global last_update
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?timeout=25&offset={last_update+1}"
    r = requests.get(url, timeout=30).json()

    if "result" in r:
        for u in r["result"]:
            last_update = u["update_id"]
            if "message" in u and "text" in u["message"]:
                chat = u["message"]["chat"]["id"]
                text = u["message"]["text"].strip()

                if chat == CHAT_ID and text == "/altin":
                    df = load_data()
                    model = train_model(df)
                    res = analyze_today(df, model)
                    send(build_report(res))

# -----------------------------
# MAIN LOOP
# -----------------------------
print("🟢 GOD'S EYE çalışıyor. Telegram'dan /altin yaz.")

while True:
    try:
        poll()
    except Exception as e:
        time.sleep(5)
