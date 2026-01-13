import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import streamlit as st
import plotly.graph_objects as go
import requests
import time
import threading
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

# =====================================================
# 1. KİMLİK VE KONFİGÜRASYON (GOD'S EYE PRO)
# =====================================================
BOT_NAME = "GOD'S EYE PRO"
TELEGRAM_TOKEN = "8217127445:AAFoFlUGleO85Harsujg5Y0dCWmxLMuCXWg"
CHAT_ID = "5600079517"

# Veri çekme motoru (Zırhlı)
def get_data(ticker, period="10y", interval="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return None

# =====================================================
# 2. HYPER-MIND YZ ÇEKİRDEĞİ
# =====================================================
class HyperMind:
    def __init__(self):
        self.rf = RandomForestRegressor(n_estimators=1000, max_depth=12, random_state=42)
        self.gb = GradientBoostingRegressor(n_estimators=1000, learning_rate=0.01, random_state=42)

    def analyze(self, df):
        df = df.copy()
        # İleri Seviye Teknik Füzyon
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA200'] = ta.ema(df['Close'], length=200)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        adx = ta.adx(df['High'], df['Low'], df['Close'])
        df['ADX'] = adx.iloc[:, 0]
        bbands = ta.bbands(df['Close'], length=20, std=2)
        df['BBL'] = bbands.iloc[:, 0]
        df['BBU'] = bbands.iloc[:, 2]
        
        # Hedef Belirleme
        df['Target'] = df['Close'].shift(-20)
        train = df.dropna()
        features = ['Close', 'RSI', 'EMA200', 'ATR', 'ADX']
        
        self.rf.fit(train[features], train['Target'])
        self.gb.fit(train[features], train['Target'])
        
        last_data = df[features].tail(1)
        pred = (self.rf.predict(last_data)[0] + self.gb.predict(last_data)[0]) / 2
        return pred, df.iloc[-1]

# =====================================================
# 3. OTOMASYON VE BİLDİRİM SİSTEMİ
# =====================================================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except:
        pass

def auto_monitor():
    """Arka planda her saat başı analiz yapar (Gelişmiş Özellik)"""
    while True:
        # Bu kısım sunucuda 7/24 çalışacak şekilde ayarlanır
        now = datetime.now()
        if now.minute == 0: # Her saat başı
            ons = get_data("GC=F")
            if ons is not None:
                mind = HyperMind()
                pred, last = mind.analyze(ons)
                # Sadece kritik değişimlerde mesaj atar
                diff = ((pred / last['Close']) - 1) * 100
                if abs(diff) > 5:
                    send_telegram(f"👁️ **{BOT_NAME} KRİTİK UYARI**\n\nBeklenen Hareket: %{diff:.2f}\nFiyat: {last['Close']:.2f}")
        time.sleep(60)

# Arka plan görevini başlat
# threading.Thread(target=auto_monitor, daemon=True).start()

# =====================================================
# 4. STREAMLIT PRO DASHBOARD
# =====================================================
st.set_page_config(page_title=BOT_NAME, layout="wide", initial_sidebar_state="expanded")

# Kenar Çubuğu (Side Bar)
with st.sidebar:
    st.title(f"👁️ {BOT_NAME}")
    st.status("Sistem: Aktif", state="running")
    st.divider()
    mode = st.radio("Analiz Modu", ["Günlük (Stabil)", "Saatlik (Agresif)"])
    st.info("Bu yazılım kurumsal düzeyde YZ modelleri kullanmaktadır.")

# Ana Ekran
t1, t2, t3 = st.tabs(["📊 Terminal", "🤖 YZ Laboratuvarı", "📞 Komuta"])

ons_df = get_data("GC=F")
usd_df = get_data("USDTRY=X")

if ons_df is not None and usd_df is not None:
    gram_f = (ons_df['Close'].iloc[-1] / 31.1035) * usd_df['Close'].iloc[-1]

    with t1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Anlık Gram Altın", f"{gram_f:.2f} TL")
        c2.metric("Ons Altın", f"{ons_df['Close'].iloc[-1]:.2f} $")
        c3.metric("Dolar/TL", f"{usd_df['Close'].iloc[-1]:.2f}")
        
        st.divider()
        fig = go.Figure(data=[go.Candlestick(x=ons_df.index[-100:], open=ons_df['Open'], high=ons_df['High'], low=ons_df['Low'], close=ons_df['Close'])])
        fig.update_layout(template="plotly_dark", height=500, title="Ons Altın - Pro Görünüm")
        st.plotly_chart(fig, use_container_width=True)

    with t2:
        if st.button("🚀 HİPER ANALİZİ ÇALIŞTIR"):
            mind = HyperMind()
            pred_ons, last_v = mind.analyze(ons_df)
            pred_gram = (pred_ons / 31.1035) * usd_df['Close'].iloc[-1]
            diff = ((pred_gram / gram_f) - 1) * 100
            
            st.subheader(f"YZ Projeksiyonu (20 Günlük)")
            st.write(f"Tahmin Edilen Fiyat: **{pred_gram:.2f} TL**")
            
            # Dinamik Direktifler
            if diff > 4:
                st.success(f"🚀 **STRATEJİ: AGRESİF ALIM**\n\nTrend Gücü (ADX): {last_v['ADX']:.2f}\nVolatilite (ATR): {last_v['ATR']:.2f}")
                karar = "AGRESİF ALIM"
            elif diff < -4:
                st.error(f"🛑 **STRATEJİ: NAKDE GEÇ**\n\nKısa vadeli sert düşüş riski tespit edildi.")
                karar = "NAKDE GEÇ"
            else:
                st.warning("⚖️ **STRATEJİ: YATAY SEYİR**\n\nPozisyonu koru, yeni ekleme yapma.")
                karar = "YATAY SEYİR"

            # Telegram'a Pro Rapor
            rapor = f"👁️ **{BOT_NAME} - PRO RAPOR**\n\n💰 Gram: {gram_f:.2f} TL\n🎯 Hedef: {pred_gram:.2f} TL\n📈 Beklenti: %{diff:.2f}\n\n🧠 **KARAR:** {karar}\n📉 **ADX:** {last_v['ADX']:.2f}"
            send_telegram(rapor)

    with t3:
        st.write("### 🎮 Komuta Merkezi")
        st.write("Telegram üzerinden komut vermek için botunuza şu mesajları atabilirsiniz:")
        st.code("/analiz\n/durum\n/ayarlar")
