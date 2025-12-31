import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.data import StockData

st.set_page_config(page_title="Symulacja", layout="wide")
st.title("🎲 Symulator Przyszłości")

st.markdown("""
Ta symulacja generuje **potencjalne ścieżki ceny** w przyszłości, bazując na historycznej zmienności (ryzyku) i średnim zwrocie danej spółki.
To nie jest wyrocznia, ale matematyczne oszacowanie prawdopodobieństwa.
""")

# --- Panel boczny ---
st.sidebar.header("Parametry Symulacji")

# Wybór spółki
default_ticker = "BTC-USD"
ticker = st.sidebar.text_input("Wpisz symbol (np. AAPL, BTC-USD):", value=default_ticker).upper().strip()

# Parametry symulacji
days_to_predict = st.sidebar.slider("Horyzont czasowy (dni w przyszłość):", min_value=30, max_value=365, value=90)
num_simulations = st.sidebar.slider("Liczba symulacji (scenariuszy):", min_value=10, max_value=500, value=200)

# Pobieranie danych historycznych
fetcher = StockData()
hist_data = fetcher.get_data(ticker, period="1y", interval="1d")

if hist_data.empty:
    st.error(f"Nie udało się pobrać danych dla {ticker}.")
    st.stop()

# --- Matematyka ---
# 1. Obliczamy dzienne zwroty logarytmiczne
log_returns = np.log(1 + hist_data["Close"].pct_change())

# 2. Wyciągamy średnią (u) i wariancję (var)
u = log_returns.mean()
var = log_returns.var()

# 3. Dryf (Drift)
drift = u - (0.5 * var)

# 4. Zmienna losowa (Odchylenie standardowe)
stdev = log_returns.std()

# Przygotowanie tablicy na wyniki
simulation_df = pd.DataFrame()

# Ostatnia znana cena
last_price = hist_data["Close"].iloc[-1]

if st.button("Uruchom Symulację 🚀"):

    with st.spinner("Generowanie alternatywnych wszechświatów..."):
        # Usunięto .values, bo stdev jest liczbą, a nie serią
        daily_volatility = stdev * np.random.normal(size=(days_to_predict, num_simulations))

        # Usunięto .values przy drift
        daily_returns = np.exp(drift + daily_volatility)

        # Tworzymy ścieżki cen
        price_paths = np.zeros((days_to_predict + 1, num_simulations))
        price_paths[0] = last_price

        for t in range(1, days_to_predict + 1):
            price_paths[t] = price_paths[t - 1] * daily_returns[t - 1]

        simulation_df = pd.DataFrame(price_paths)

    # --- Wykres ---
    fig = go.Figure()

    # Rysujemy każdą ścieżkę (limit do 100 dla wydajności)
    limit_lines = min(num_simulations, 100)

    for i in range(limit_lines):
        fig.add_trace(go.Scatter(
            y=simulation_df[i],
            mode='lines',
            line=dict(width=1, color='rgba(100, 100, 255, 0.2)'),
            showlegend=False,
            hoverinfo='skip'
        ))

    # Dodajemy linię średnią
    mean_path = simulation_df.mean(axis=1)
    fig.add_trace(go.Scatter(
        y=mean_path,
        mode='lines',
        name='Średnia (Oczekiwana)',
        line=dict(width=4, color='white')
    ))

    # Ostatnia cena historyczna
    fig.add_annotation(x=0, y=last_price, text=f"Start: {last_price:.2f}", showarrow=True, arrowhead=1)

    # Końcowa średnia cena
    final_mean = mean_path.iloc[-1]
    fig.add_annotation(x=days_to_predict, y=final_mean, text=f"Średnia: {final_mean:.2f}", showarrow=True, arrowhead=1,
                       ax=20)

    fig.update_layout(
        title=f"Symulacja Monte Carlo dla {ticker} ({days_to_predict} dni)",
        xaxis_title="Dni w przyszłość",
        yaxis_title="Cena Symulowana",
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- Podsumowanie statystyczne ---
    st.subheader("📊 Analiza Ryzyka")

    final_prices = simulation_df.iloc[-1]

    col1, col2, col3 = st.columns(3)
    col1.metric("Pesymistyczny", f"{np.percentile(final_prices, 5):.2f}", delta_color="inverse")
    col2.metric("Średni (Mediana)", f"{np.median(final_prices):.2f}")
    col3.metric("Optymistyczny", f"{np.percentile(final_prices, 95):.2f}")

    st.info(
        "Pamiętaj: Model zakłada, że przyszłość będzie zachowywać się statystycznie podobnie do przeszłości. 'Czarne Łabędzie' nie są tu uwzględnione!")