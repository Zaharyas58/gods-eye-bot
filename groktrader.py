import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import streamlit as st
import plotly.graph_objects as go
import requests
import threading
import time
from datetime import datetime
from sklearn.ensemble import GradientBoostingRegressor

# =====================================================
# 1. KİMLİK VE AYARLAR
# =====================================================
BOT_NAME = "GOD'S EYE SUPREME"
TELEGRAM_TOKEN = "8217127445:AAFoFlUGleO85Harsujg5Y0dCWmxLMuCXWg"
CHAT_ID = "5600079517"

# =====================================================
# 2. HESAPLAMA VE VERİ MOTORU (GÜÇLENDİRİLDİ)
# =====================================================
def get_clean_data(ticker):
    try:
        df = yf.download(ticker, period="5y", interval="1d", progress=False, auto_adjust=True)
        # Çoklu sütun yapısını (Multi-index) temizle
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return None

def analyze_market():
    ons_df = get_clean_data("GC=F")
    usd_df = get_clean_data("USDTRY=X")
    dxy_df = get_clean_data("DX-Y.NYB")
    
    if ons_df is None or usd_df is None:
        return None

    # Teknik Analiz
    ons_df['RSI'] = ta.rsi(ons_df['Close'], length=14)
    ons_df['ADX'] = ta.adx(ons_df['High'], ons_df['Low'], ons_df['Close']).iloc[:, 0]
    ons_df['DXY'] = dxy_df['Close']
    
    # YZ Tahmini (Basitleştirilmiş ve Hızlı)
    ons_df['Target'] = ons_df['Close'].shift(-15)
    train = ons_df.dropna()
    features = ['Close', 'RSI', 'ADX', 'DXY']
    
    model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    model.fit(train[features], train['Target'])
    
    # Son Değerler
    last_row = ons_df[features].tail(1)
    pred_ons = float(model.predict(last_row)[0])
    
    current_ons = float(ons_df['Close'].iloc[-1])
    current_usd = float(usd_df['Close'].iloc[-1])
    
    # GRAM HESABI
    gram_now = (current_ons / 31.1035) * current_usd
    gram_target = (pred_ons / 31.1035) * current_usd
    
    return {
        "gram_now": gram_now,
        "gram_target": gram_target,
        "ons": current_ons,
        "adx": float(ons_df['ADX'].iloc[-1])
    }

# =====================================================
# 3. TELEGRAM MESAJ KONTROLÜ (MESAJ YAĞMURUNU ENGELLER)
# =====================================================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

def telegram_listener():
    # offset= -1 yaparak sadece bot açıldıktan SONRA gelen mesajları almasını sağlıyoruz
    last_update_id = 0
    
    # Başlangıçta eski mesajları temizle
    init_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset=-1"
    try:
        init_res = requests.get(init_url).json()
        if "result" in init_res and len(init_res["result"]) > 0:
            last_update_id = init_res["result"][-1]["update_id"]
    except:
        pass

    while True:
        try:
            # Sadece yeni mesajları getir (offset kullanarak)
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            response = requests.get(url, timeout=35).json()
            
            if "result" in response:
                for update in response["result"]:
                    last_update_id = update["update_id"]
                    
                    if "message" in update and "text" in update["message"]:
                        user_msg = update["message"]["text"]
                        
                        if user_msg == "/analiz":
                            res = analyze_market()
                            if res:
                                diff = ((res['gram_target'] / res['gram_now']) - 1) * 100
                                report = (f"👁️ **{BOT_NAME} ANALİZ**\n\n"
                                          f"💰 Gram: {res['gram_now']:.2f} TL\n"
                                          f"🎯 Hedef: {res['gram_target']:.2f} TL\n"
                                          f"📈 Fark: %{diff:.2f}\n\n"
                                          f"🔍 Ons: {res['ons']:.2f}$\n"
                                          f"💪 Güç: {res['adx']:.1f}")
                                send_telegram(report)
                            else:
                                send_telegram("❌ Veri çekilemedi, tekrar deneyin.")
                        
                        elif user_msg == "/haber":
                            send_telegram("🌍 **HABER:** ABD Tarım Dışı İstihdam verisi bekleniyor, piyasa yatay.")
                            
        except Exception as e:
            time.sleep(5)
        time.sleep(1)

# Dinleyiciyi başlat (Tek seferlik)
if 'bot_v34_running' not in st.session_state:
    threading.Thread(target=telegram_listener, daemon=True).start()
    st.session_state.bot_v34_running = True

# =====================================================
# 4. ARAYÜZ
# =====================================================
st.title(f"🛡️ {BOT_NAME} V34")
st.success("Telegram dinleyicisi stabilize edildi. Mesaj döngüsü kırıldı.")
if st.button("MANUEL ANALİZ"):
    r = analyze_market()
    st.write(r)
