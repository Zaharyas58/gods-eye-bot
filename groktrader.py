import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import streamlit as st
import requests
import threading
import time
import os
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime

# =====================================================
# 1. KONFİGÜRASYON VE ZOMBİ KONTROLÜ
# =====================================================
BOT_NAME = "GOD'S EYE PROPHET V40"
TELEGRAM_TOKEN = "8217127445:AAFoFlUGleO85Harsujg5Y0dCWmxLMuCXWg"
CHAT_ID = "5600079517"

# Zombi Thread Engelleyici: Python'un çalışma alanında bu thread varsa bir daha açma
def start_bot_once():
    # Streamlit'in kendi içindeki thread yönetimini değil, Python'un aktif threadlerini sayıyoruz
    for t in threading.enumerate():
        if t.name == "GodsEyeWorker":
            return # Zaten çalışıyor, ikinciyi açma!

    worker = threading.Thread(target=telegram_worker, name="GodsEyeWorker", daemon=True)
    worker.start()

# =====================================================
# 2. VERİ VE ML MOTORU (CACHE'LENMİŞ)
# =====================================================
@st.cache_data(ttl=3600) # Veriyi 1 saatte bir tazeler, CPU'yu korur
def get_optimized_data():
    assets = {"ONS": "GC=F", "DXY": "DX-Y.NYB", "SPY": "SPY", "VIX": "^VIX", "USD": "USDTRY=X"}
    dfs = {k: yf.download(v, period="2y", interval="1d", progress=False, auto_adjust=True)['Close'] for k, v in assets.items()}
    
    df = pd.concat(dfs.values(), axis=1, keys=dfs.keys()).dropna()
    
    # Değişim Oranları (Returns)
    df['ons_ret'] = df['ONS'].pct_change()
    df['dxy_ret'] = df['DXY'].pct_change()
    df['vix_spike'] = (df['VIX'].pct_change() > 0.15).astype(int)
    
    # Volatilite Bazlı Hedef (Prophet Modu)
    vol = df['ons_ret'].rolling(10).std()
    df['target'] = ((df['ONS'].shift(-10) - df['ONS']) / df['ONS'] > (1.5 * vol)).astype(int)
    
    return df.dropna()

def train_and_predict():
    df = get_optimized_data()
    features = ['ONS', 'DXY', 'VIX', 'ons_ret', 'dxy_ret', 'vix_spike']
    
    X = df[features]
    y = df['target']
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    last_row = df[features].tail(1)
    prob = model.predict_proba(last_row)[0][1] * 100
    
    ons_now = float(df['ONS'].iloc[-1])
    usd_now = float(df['USD'].iloc[-1])
    gram_now = (ons_now / 31.1035) * usd_now
    
    return gram_now, prob, ons_now

# =====================================================
# 3. TELEGRAM LİSTENER (ZOMBİSİZ)
# =====================================================
def telegram_worker():
    last_id = 0
    # Açılışta eski birikmiş mesajları bir kere temizle
    try:
        init = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset=-1").json()
        if init.get("result"): last_id = init["result"][-1]["update_id"]
    except: pass

    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_id + 1}&timeout=30"
            res = requests.get(url).json()
            
            if res.get("result"):
                for upd in res["result"]:
                    last_id = upd["update_id"]
                    if "message" in upd and "text" in upd["message"]:
                        if upd["message"]["text"] == "/analiz":
                            g, p, o = train_and_predict()
                            msg = (f"🔮 **{BOT_NAME}**\n\n"
                                   f"💰 **Gram:** {g:.2f} TL\n"
                                   f"🔥 **Patlama Olasılığı:** %{p:.1f}\n"
                                   f"📉 **Ons Altın:** {o:.2f} $\n"
                                   f"🛡️ *Durum: Zombi Koruma Aktif*")
                            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                                          json={"chat_id": CHAT_ID, "text": msg})
        except: time.sleep(10)
        time.sleep(2)

# =====================================================
# 4. ÇALIŞTIRMA
# =====================================================
start_bot_once()

st.title(f"🛡️ {BOT_NAME}")
st.success("Thread sızıntısı ve zombi bot sorunu Singleton mimarisi ile çözüldü.")
st.write("Telegram üzerinden `/analiz` göndererek test edin. Artık sadece 1 cevap alacaksınız.")
