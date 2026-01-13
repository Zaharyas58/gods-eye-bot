import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import streamlit as st
import plotly.graph_objects as go
import requests
import os
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

# =====================================================
# 1. GOD'S EYE KİMLİK VE BAĞLANTI
# =====================================================
BOT_NAME = "GOD'S EYE"
TELEGRAM_TOKEN = "8217127445:AAFoFlUGleO85Harsujg5Y0dCWmxLMuCXWg"
CHAT_ID = "5600079517"

def veri_cek_temiz(ticker):
    try:
        df = yf.download(ticker, period="10y", interval="1d", progress=False, auto_adjust=True)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return None

# =====================================================
# 2. ANALİZ ÇEKİRDEĞİ
# =====================================================
class GodsEyeCore:
    def __init__(self):
        self.rf = RandomForestRegressor(n_estimators=500, max_depth=10, random_state=42)
        self.gb = GradientBoostingRegressor(n_estimators=500, learning_rate=0.01, random_state=42)

    def derin_analiz(self, df):
        df = df.copy()
        # İleri Teknik Göstergeler
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA200'] = ta.ema(df['Close'], length=200)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        # ADX ve Bollinger (Sütun bağımsız güvenli çekim)
        adx_df = ta.adx(df['High'], df['Low'], df['Close'])
        df['ADX'] = adx_df.iloc[:, 0]
        bbands = ta.bbands(df['Close'], length=20, std=2)
        df['BBL'] = bbands.iloc[:, 0]
        df['BBU'] = bbands.iloc[:, 2]
        
        # YZ Hedefleme
        df['Target'] = df['Close'].shift(-20)
        train_df = df.dropna()
        
        features = ['Close', 'RSI', 'EMA200', 'ATR', 'ADX']
        X = train_df[features]
        y = train_df['Target']
        
        self.rf.fit(X, y)
        self.gb.fit(X, y)
        
        last_row = df[features].tail(1)
        tahmin = (self.rf.predict(last_row)[0] + self.gb.predict(last_row)[0]) / 2
        
        return tahmin, df.iloc[-1]

# =====================================================
# 3. ARAYÜZ
# =====================================================
st.set_page_config(page_title=BOT_NAME, layout="wide")
st.title(f"👁️ {BOT_NAME} - Altın Yatırım Terminali")

ons_df = veri_cek_temiz("GC=F")
usd_df = veri_cek_temiz("USDTRY=X")

if ons_df is not None and usd_df is not None:
    su_an_ons = ons_df['Close'].iloc[-1]
    dolar_f = usd_df['Close'].iloc[-1]
    gram_f = (su_an_ons / 31.1035) * dolar_f

    st.header(f"💰 Anlık Gram Altın: {gram_f:.2f} TL")
    
    if st.button(f"🔮 {BOT_NAME} ANALİZİNİ BAŞLAT"):
        with st.spinner(f"{BOT_NAME} küresel verileri süzüyor..."):
            core = GodsEyeCore()
            tahmin_ons, son_veri = core.derin_analiz(ons_df)
            tahmin_gram = (tahmin_ons / 31.1035) * dolar_f
            
            yuzde = ((tahmin_gram / gram_f) - 1) * 100
            
            # Stratejik Direktifler
            st.divider()
            if yuzde > 3:
                karar = "🔥 AGRESİF ALIM SİNYALİ"
                st.success(karar)
            elif yuzde < -3:
                karar = "⚠️ NAKDE GEÇİŞ UYARISI"
                st.error(karar)
            else:
                karar = "⚖️ YATAY SEYİR / İZLEMEDE KAL"
                st.warning(karar)

            st.metric("20 Günlük Hedef", f"{tahmin_gram:.2f} TL", f"%{yuzde:.2f}")

            # Telegram Raporu
            msg = f"👁️ **{BOT_NAME} RAPORU**\n\n💰 Gram: {gram_f:.2f} TL\n🎯 Hedef: {tahmin_gram:.2f} TL\n📈 Tahmin: %{yuzde:.2f}\n\n📢 **STRATEJİ:** {karar}"
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg})

with st.sidebar:
    st.image("https://img.icons8.com/ios-filled/100/ffffff/eye.png")
    st.write(f"### {BOT_NAME} Status: Online")
    st.info("Fiziki altın yatırımı için optimize edilmiştir.")