import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import streamlit as st
import plotly.graph_objects as go
import requests
import threading
import time
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

# =====================================================
# 1. KİMLİK VE KONFİGÜRASYON
# =====================================================
BOT_NAME = "GOD'S EYE PRO"
TELEGRAM_TOKEN = "8217127445:AAFoFlUGleO85Harsujg5Y0dCWmxLMuCXWg"
CHAT_ID = "5600079517"

# Veri motoru
def get_data(ticker):
    df = yf.download(ticker, period="10y", interval="1d", progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    return df

# =====================================================
# 2. HYPER-MIND ANALİZ MOTORU
# =====================================================
def analyze_engine():
    ons_df = get_data("GC=F")
    usd_df = get_data("USDTRY=X")
    
    # Teknik Göstergeler
    ons_df['RSI'] = ta.rsi(ons_df['Close'], length=14)
    ons_df['EMA200'] = ta.ema(ons_df['Close'], length=200)
    ons_df['Target'] = ons_df['Close'].shift(-20)
    
    train = ons_df.dropna()
    model = RandomForestRegressor(n_estimators=500, random_state=42)
    model.fit(train[['Close', 'RSI', 'EMA200']], train['Target'])
    
    last_v = ons_df[['Close', 'RSI', 'EMA200']].tail(1)
    pred_ons = model.predict(last_v)[0]
    
    gram_now = (ons_df['Close'].iloc[-1] / 31.1035) * usd_df['Close'].iloc[-1]
    gram_target = (pred_ons / 31.1035) * usd_df['Close'].iloc[-1]
    diff = ((gram_target / gram_now) - 1) * 100
    
    return gram_now, gram_target, diff

# =====================================================
# 3. TELEGRAM KOMUT DİNLEYİCİ (INTERACTIVE)
# =====================================================
def send_msg(text):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

def telegram_listener():
    last_update_id = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            response = requests.get(url).json()
            
            if "result" in response:
                for update in response["result"]:
                    last_update_id = update["update_id"]
                    if "message" in update and "text" in update["message"]:
                        komut = update["message"]["text"]
                        
                        if komut == "/analiz":
                            send_msg("👁️ **Analiz Başlatıldı... Bekleyin.**")
                            now, target, diff = analyze_engine()
                            msg = f"👁️ **GOD'S EYE ANALİZ RAPORU**\n\n💰 Gram: {now:.2f} TL\n🎯 Hedef: {target:.2f} TL\n📈 Beklenti: %{diff:.2f}"
                            send_msg(msg)
                        
                        elif komut == "/durum":
                            send_msg(f"🛡️ {BOT_NAME} Sistemi Online.\n📊 Veri Akışı: Aktif\n🧠 Yapay Zeka: Hiper-Mod")
                            
        except Exception as e:
            print(f"Hata: {e}")
        time.sleep(2)

# Dinleyiciyi bir kez başlat (Streamlit her yenilendiğinde tekrar başlamasın diye kontrol)
if 'bot_started' not in st.session_state:
    threading.Thread(target=telegram_listener, daemon=True).start()
    st.session_state['bot_started'] = True

# =====================================================
# 4. ARAYÜZ
# =====================================================
st.title(f"🛡️ {BOT_NAME} DASHBOARD")
st.write("Telegram'dan `/analiz` yazarak botu tetikleyebilirsiniz.")

if st.button("MANUEL ANALİZ"):
    n, t, d = analyze_engine()
    st.metric("Gram Altın Hedef", f"{t:.2f} TL", f"%{d:.2f}")
