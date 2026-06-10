import streamlit as st
import yfinance as yf
import pandas as pd
from src.config import MARKET_INDICES

st.set_page_config(page_title="Smart Portfolio Studio", layout="wide", page_icon="📈")

st.title("🚀 Smart Portfolio Studio")
st.markdown("### Centrum dowodzenia Twoimi finansami")

# --- SZYBKI PODGLĄD RYNKU ---
st.markdown("---")
st.markdown("#### 🌍 Puls Rynku (Na żywo)")
col1, col2, col3, col4 = st.columns(4)


def get_market_change(ticker):
    try:
        data = yf.Ticker(ticker).fast_info
        change = ((data.last_price - data.previous_close) / data.previous_close) * 100
        return data.last_price, change
    except:
        return 0.0, 0.0


cols = [col1, col2, col3, col4]
for (name, ticker), col in zip(MARKET_INDICES.items(), cols):
    price, change = get_market_change(ticker)

    with col:
        with st.container(border=True):
            st.metric(
                label=name,
                value=f"{price:,.2f}",
                delta=f"{change:+.2f}%"
            )

st.markdown("---")

# --- NAWIGACJA / OPIS ---
c1, c2 = st.columns([2, 1])

with c1:
    with st.container(border=True):
        st.info("👈 **Użyj menu po lewej**, aby nawigować między modułami.")
        st.subheader("🛠️ Dostępne Moduły:")
        st.markdown("""
        * 📊 **Analiza:** Szczegółowe wykresy, wskaźniki (RSI, MACD), fundamenty i diagnoza AI.
        * 💼 **Portfel:** Twój osobisty rejestr inwestycji. Obsługuje waluty i strategie ETF.
        * 🔮 **Symulacje:** Obliczanie procentu składanego i prognoz na lata.
        * 🔗 **Korelacje:** Mapa powiązań między Twoimi aktywami.
        * 🕹️ **Symulator:** Testowanie strategii na danych historycznych.
        * 🧠 **Optymalizator:** Algorytm Markowitza do budowy idealnego portfela.
        """)

with c2:
    with st.container(border=True):
        st.success("💡 **Cytat Dnia:**")
        st.markdown("> *„Rynek to mechanizm przenoszenia pieniędzy od niecierpliwych do cierpliwych.”*")
        st.caption("— Warren Buffett")