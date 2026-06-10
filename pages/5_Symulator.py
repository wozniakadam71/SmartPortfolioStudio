import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.data import StockData

st.set_page_config(page_title="Symulacja Monte Carlo", layout="wide")
st.title("🎲 Symulator Scenariuszy (Monte Carlo)")

with st.container(border=True):
    st.markdown("""
    Ta symulacja generuje **potencjalne ścieżki ceny** w przyszłości, bazując na historycznej zmienności (ryzyku) i średnim zwrocie danej spółki.
    To nie jest wyrocznia, ale **matematyczne oszacowanie prawdopodobieństwa**.
    """)

# Panel boczny
st.sidebar.header("🎛️ Parametry Symulacji")
default_ticker = "BTC-USD"
ticker = st.sidebar.text_input("Wpisz symbol (np. AAPL, BTC-USD):", value=default_ticker).upper().strip()
days_to_predict = st.sidebar.slider("Horyzont czasowy (dni w przyszłość):", min_value=30, max_value=365, value=90)
num_simulations = st.sidebar.slider("Liczba symulacji (scenariuszy):", min_value=10, max_value=500, value=200)

# Pobieranie danych historycznych
fetcher = StockData()
hist_data = fetcher.get_data(ticker, period="1y", interval="1d")

if hist_data.empty:
    st.error(f"Nie udało się pobrać danych dla {ticker}.")
    st.stop()

# Matematyka
log_returns = np.log(1 + hist_data["Close"].pct_change())
u = log_returns.mean()
var = log_returns.var()
drift = u - (0.5 * var)
stdev = log_returns.std()
last_price = hist_data["Close"].iloc[-1]

st.markdown("---")

if st.button("🚀 Uruchom Symulację"):
    with st.spinner("Generowanie alternatywnych wszechświatów... 🌌"):
        daily_volatility = stdev * np.random.normal(size=(days_to_predict, num_simulations))
        daily_returns = np.exp(drift + daily_volatility)

        price_paths = np.zeros((days_to_predict + 1, num_simulations))
        price_paths[0] = last_price

        for t in range(1, days_to_predict + 1):
            price_paths[t] = price_paths[t - 1] * daily_returns[t - 1]

        simulation_df = pd.DataFrame(price_paths)

    # Wykres w kafelku
    with st.container(border=True):
        fig = go.Figure()
        limit_lines = min(num_simulations, 100)

        for i in range(limit_lines):
            fig.add_trace(go.Scatter(
                y=simulation_df[i], mode='lines', line=dict(width=1, color='rgba(100, 100, 255, 0.2)'),
                showlegend=False, hoverinfo='skip'
            ))

        mean_path = simulation_df.mean(axis=1)
        fig.add_trace(
            go.Scatter(y=mean_path, mode='lines', name='Średnia Oczekiwana', line=dict(width=4, color='white')))
        fig.add_annotation(x=0, y=last_price, text=f"Start: {last_price:.2f}", showarrow=True, arrowhead=1)
        final_mean = mean_path.iloc[-1]
        fig.add_annotation(x=days_to_predict, y=final_mean, text=f"Średnia: {final_mean:.2f}", showarrow=True,
                           arrowhead=1, ax=20)

        fig.update_layout(
            title=f"Wizualizacja Ścieżek dla {ticker} ({days_to_predict} dni)",
            xaxis_title="Dni w przyszłość", yaxis_title="Cena Symulowana",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    # Podsumowanie w kafelkach
    st.subheader("📊 Analiza Ryzyka (Wynik za N dni)")
    final_prices = simulation_df.iloc[-1]

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.metric("Pesymistyczny (5%)", f"{np.percentile(final_prices, 5):.2f}", delta_color="inverse")
    with col2:
        with st.container(border=True):
            st.metric("Średni (Mediana)", f"{np.median(final_prices):.2f}")
    with col3:
        with st.container(border=True):
            st.metric("Optymistyczny (95%)", f"{np.percentile(final_prices, 95):.2f}")

    with st.container(border=True):
        st.info(
            "**Jak to czytać?** Model sugeruje, że z 90% prawdopodobieństwem cena "
            "znajdzie się w przedziale między scenariuszem pesymistycznym a optymistycznym."
        )

# Disclaimer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: small;'>
        <b>Nota prawna:</b> Aplikacja służy wyłącznie celom edukacyjnym i informacyjnym. 
        Prezentowane dane nie stanowią porady inwestycyjnej.
    </div>
    """,
    unsafe_allow_html=True
)