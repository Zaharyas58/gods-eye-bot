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

# =====================================================
# 1. KİMLİK VE KESİN KİLİT MEKANİZMASI
# =====================================================
BOT_NAME = "GOD'S EYE PROPHET V41"
TELEGRAM_TOKEN = "8217127445:AAFoFlUGleO85Harsujg5Y0dCWmxLMuCXWg"
CHAT_ID = "5600079517"

# Streamlit her başladığında benzersiz bir kimlik alır
if 'app_instance_id' not in st.session_state:
    st.session_state.app_instance_id = str(time.time())

# =====================================================
# 2. ANALİZ MOTORU (V39'UN KAHİN GÜCÜ)
# =====================================================
def get_prophet_analysis():
    # Veri çekme ve hizalama (Inner Join)
    assets = {"ONS": "GC=F", "DXY": "DX-Y.NYB", "VIX": "^VIX", "USD": "USDTRY=X"}
    dfs = {k: yf.download(v, period="1y", interval="1d", progress=False, auto_adjust=True)['Close'] for k, v in assets.items()}
    df = pd.concat(dfs.values(), axis=1, keys=dfs.keys()).dropna()
    
    # Değişim ve Volatilite (Breakout Target)
    df['ons_ret'] = df['ONS'].pct_change()
    vol = df['ons_ret'].rolling(10).std()
    df['target'] = ((df['ONS'].shift(-10) - df['ONS']) / df['ONS'] > (1.5 * vol)).astype(int)
    
    train = df.dropna()
    features = ['ONS', 'DXY', 'VIX']
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(train[features], train['target'])
    
    prob = model.predict_proba(df[features].tail(1))[0][1] * 100
    ons_now = float(df['ONS'].iloc[-1])
    usd_now = float(df['USD'].iloc[-1])
    
    return (ons_now / 31.1035) * usd_now, prob, ons_now

# =====================================================
# 3. ZOMBİ SAVAR TELEGRAM LİSTENER
# =====================================================
def telegram_worker(instance_id):
    last_id = 0
    # Açılışta geçmiş mesajları temizlemek için offset=-1
    try:
        init = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset=-1").json()
        if init.get("result"): last_id = init["result"][-1]["update_id"]
    except: pass

    while True:
        # EĞER BU THREAD, GÜNCEL APP ID İLE EŞLEŞMİYORSA KENDİNİ ÖLDÜR
        if instance_id != st.session_state.app_instance_id:
            break # Eski thread (zombi) burada intihar eder.

        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_id + 1}&timeout=10"
            res = requests.get(url).json()
            if res.get("result"):
                for upd in res["result"]:
                    last_id = upd["update_id"]
                    if "message" in upd and "text" in upd["message"]:
                        if upd["message"]["text"] == "/analiz":
                            g, p, o = get_prophet_analysis()
                            msg = f"🔮 **{BOT_NAME}**\n💰 Gram: {g:.2f} TL\n🔥 Patlama: %{p:.1f}\n📈 Ons: {o:.2f}$"
                            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                                          json={"chat_id": CHAT_ID, "text": msg})
        except: time.sleep(5)
        time.sleep(1)

# =====================================================
# 4. KESİN ÇALIŞTIRMA KONTROLÜ
# =====================================================
if 'worker_started' not in st.session_state:
    st.session_state.worker_started = True
    threading.Thread(target=telegram_worker, args=(st.session_state.app_instance_id,), daemon=True).start()

st.title(f"🛡️ {BOT_NAME}")
st.write(f"Sistem Kimliği: `{st.session_state.app_instance_id}`")
st.info("Eski kopyalar (zombiler) sistem kimliği uyuşmazlığı nedeniyle otomatik kapatılır.")
