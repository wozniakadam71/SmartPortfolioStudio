import streamlit as st
import pandas as pd
import plotly.express as px
from src.data import StockData

st.set_page_config(page_title="Macierz Korelacji", layout="wide")
st.title("🔗 Macierz Korelacji Portfela")

st.markdown("""
Sprawdź, czy Twój portfel jest dobrze zdywersyfikowany.
Wpisz swoje spółki w panelu bocznym lub wybierz z listy popularnych.
""")

# --- Panel Boczny: Konfiguracja ---
st.sidebar.header("Ustawienia Macierzy")

# 1. Lista popularnych (dla wygody)
popular_tickers = [
    "BTC-USD", "ETH-USD", "SPY", "QQQ", "GLD",
    "NVDA", "TSLA", "MSFT", "AAPL", "GOOGL",
    "CDPROJEKT.WA", "KGH.WA", "PKO.WA", "ORLEN.WA", "XTB.WA"
]

selected_from_list = st.sidebar.multiselect(
    "Wybierz z popularnych (opcjonalne):",
    options=popular_tickers,
    default=["BTC-USD", "SPY", "GLD"]  # Domyślny startowy zestaw
)

# 2. Pole na własne spółki (kluczowa zmiana)
st.sidebar.markdown("---")
manual_tickers_input = st.sidebar.text_area(
    "Lub wpisz własne (oddzielone przecinkiem):",
    placeholder="np. PEP, KO, DNP.WA, ALR.WA",
    help="Wpisz tutaj dowolne symbole z Yahoo Finance oddzielone przecinkami."
)

# --- Logika łączenia list ---
# Rozbijamy wpisany tekst na listę, usuwamy spacje i zamieniamy na wielkie litery
manual_tickers = []
if manual_tickers_input:
    manual_tickers = [x.strip().upper() for x in manual_tickers_input.split(",") if x.strip()]

# Łączymy obie listy i usuwamy duplikaty (set)
final_ticker_list = list(set(selected_from_list + manual_tickers))

st.sidebar.markdown(f"**Wybrano łącznie:** {len(final_ticker_list)} aktywów")

# 3. Wybór okresu
period = st.sidebar.selectbox(
    "Okres danych:",
    options=["3mo", "6mo", "1y", "2y", "5y"],
    index=2
)

# Zabezpieczenie: musi być min. 2 spółki
if len(final_ticker_list) < 2:
    st.info("👈 Wybierz lub wpisz przynajmniej dwie spółki w panelu bocznym, aby zobaczyć korelację.")
    st.stop()

# --- Pobieranie i Przetwarzanie Danych ---
if st.button("Oblicz Korelację 🚀"):
    fetcher = StockData()
    combined_df = pd.DataFrame()

    progress_bar = st.progress(0)

    with st.spinner("Pobieranie danych..."):
        for i, ticker in enumerate(final_ticker_list):
            # Pobieramy dane
            df = fetcher.get_data(ticker, period=period, interval="1d")

            if not df.empty and "Close" in df.columns:
                # Obliczamy dzienne zwroty procentowe
                combined_df[ticker] = df["Close"].pct_change()

            # Aktualizacja paska postępu
            progress_bar.progress((i + 1) / len(final_ticker_list))

    # Usuwamy pierwszy wiersz (NaN po pct_change)
    combined_df = combined_df.dropna()

    if combined_df.empty:
        st.error("Nie udało się pobrać wystarczających danych. Sprawdź, czy wpisane symbole są poprawne.")
    else:
        # --- Obliczanie Korelacji ---
        corr_matrix = combined_df.corr()

        # --- Wizualizacja (Heatmapa Plotly) ---
        fig = px.imshow(
            corr_matrix,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="RdBu_r",  # Czerwony (1.0) - Niebieski (-1.0)
            zmin=-1, zmax=1,
            title=f"Korelacja portfela ({period})"
        )

        fig.update_layout(
            height=700,
            xaxis_title=None,
            yaxis_title=None
        )

        st.plotly_chart(fig, use_container_width=True)

        # --- Inteligentne Wnioski ---
        st.subheader("💡 Wnioski:")

        # Szukamy najsilniejszej pary
        c = corr_matrix.abs()
        # Wypełniamy przekątną zerami, żeby nie znajdowało korelacji 1.0 samej ze sobą
        for col in c.columns:
            c.loc[col, col] = 0

        s = c.unstack()
        so = s.sort_values(kind="quicksort", ascending=False)

        if not so.empty:
            top_pair = so.index[0]
            top_val = corr_matrix.loc[top_pair[0], top_pair[1]]  # Pobieramy oryginalną wartość (+/-)

            st.info(f"Najsilniejsze powiązanie: **{top_pair[0]}** i **{top_pair[1]}** (Korelacja: {top_val:.2f}).")

            if top_val > 0.8:
                st.warning(
                    "⚠️ **Wysokie ryzyko koncentracji!** Te dwa aktywa chodzą niemal identycznie. Jeśli jedno spadnie, drugie prawdopodobnie też.")
            elif top_val < 0.2 and top_val > -0.2:
                st.success("✅ Znaleziono aktywa nieskorelowane. To dobrze wpływa na bezpieczeństwo portfela.")