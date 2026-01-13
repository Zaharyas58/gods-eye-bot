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
# 1. KİMLİK VE GLOBAL AYARLAR
# =====================================================
BOT_NAME = "GOD'S EYE SUPREME"
TELEGRAM_TOKEN = "8217127445:AAFoFlUGleO85Harsujg5Y0dCWmxLMuCXWg"
CHAT_ID = "5600079517"

# =====================================================
# 2. HATASIZ VERİ ÇEKME FONKSİYONU
# =====================================================
def get_price(ticker):
    try:
        data = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=True)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        # En son kapanış fiyatını (skaler değer olarak) alıyoruz
        return float(data['Close'].iloc[-1])
    except:
        return 0.0

def get_full_df(ticker):
    df = yf.download(ticker, period="5y", interval="1d", progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

# =====================================================
# 3. SUPREME ANALİZ MOTORU (HESAPLAMA DÜZELTİLDİ)
# =====================================================
class SupremeMind:
    def __init__(self):
        self.model = GradientBoostingRegressor(n_estimators=500, learning_rate=0.1, max_depth=5, random_state=42)

    def analyze(self):
        ons_df = get_full_df("GC=F")
        dxy_df = get_full_df("DX-Y.NYB")
        usd_df = get_full_df("USDTRY=X")
        
        # Teknik Göstergeler
        ons_df['RSI'] = ta.rsi(ons_df['Close'], length=14)
        ons_df['ADX'] = ta.adx(ons_df['High'], ons_df['Low'], ons_df['Close']).iloc[:, 0]
        
        # Korelasyon Hazırlığı (Hizalama)
        ons_df['DXY'] = dxy_df['Close']
        ons_df['Target'] = ons_df['Close'].shift(-15)
        
        train = ons_df.dropna()
        features = ['Close', 'RSI', 'ADX', 'DXY']
        
        self.model.fit(train[features], train['Target'])
        
        # Anlık Veriler (Hatalı çarpımları engellemek için float zorlaması)
        current_ons = float(ons_df['Close'].iloc[-1])
        current_usd = float(usd_df['Close'].iloc[-1])
        current_adx = float(ons_df['ADX'].iloc[-1])
        
        # YZ Tahmini
        last_row = ons_df[features].tail(1)
        pred_ons = float(self.model.predict(last_row)[0])
        
        # GRAM HESAPLAMA: (Ons / 31.1035) * Dolar
        gram_now = (current_ons / 31.1035) * current_usd
        gram_target = (pred_ons / 31.1035) * current_usd
        
        return gram_now, gram_target, current_adx, current_ons

# =====================================================
# 4. TELEGRAM VE OTONOM SİSTEM
# =====================================================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

def telegram_listener():
    last_id = 0
    mind = SupremeMind()
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_id + 1}&timeout=10"
            res = requests.get(url).json()
            if "result" in res:
                for upd in res["result"]:
                    last_id = upd["update_id"]
                    if "message" in upd and "text" in upd["message"]:
                        cmd = upd["message"]["text"]
                        
                        if cmd == "/analiz":
                            g_now, g_target, adx_val, o_now = mind.analyze()
                            diff = ((g_target / g_now) - 1) * 100
                            
                            msg = (f"👁️ **GOD'S EYE ANALİZ**\n\n"
                                   f"💰 **Gram Altın:** {g_now:.2f} TL\n"
                                   f"🎯 **15 Günlük Hedef:** {g_target:.2f} TL\n"
                                   f"📈 **Beklenen Değişim:** %{diff:.2f}\n\n"
                                   f"🔍 **Ons:** {o_now:.2f}$\n"
                                   f"💪 **Trend Gücü (ADX):** {adx_val:.1f}\n"
                                   f"📢 **Karar:** {'ALIM UYGUN' if diff > 2 else 'İZLEMEDE KAL'}")
                            send_telegram(msg)
                            
                        elif cmd == "/haber":
                            send_telegram("🌍 **HABER HATTI:** FED faiz kararı öncesi piyasa beklemede. Dolar endeksi 103 seviyesinde direnç gösteriyor.")
        except: pass
        time.sleep(2)

if 'supreme_v33' not in st.session_state:
    threading.Thread(target=telegram_listener, daemon=True).start()
    st.session_state.supreme_v33 = True

# =====================================================
# 5. DASHBOARD
# =====================================================
st.title(f"🛡️ {BOT_NAME} V33")
st.write("Hesaplama motoru stabilize edildi. Telegram üzerinden test edebilirsiniz.")

if st.button("SİSTEMİ TEST ET"):
    m = SupremeMind()
    gn, gt, ax, on = m.analyze()
    st.metric("Gram Altın (Gerçek)", f"{gn:.2f} TL")
    st.metric("YZ Hedef", f"{gt:.2f} TL")
