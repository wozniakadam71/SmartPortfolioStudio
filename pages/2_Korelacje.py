import streamlit as st
import pandas as pd
import plotly.express as px
from src.data import StockData

st.set_page_config(page_title="Macierz Korelacji", layout="wide")
st.title("Macierz Korelacji Portfela")

st.markdown("""
Sprawdź, czy Twój portfel jest dobrze zdywersyfikowany.
Wpisz swoje spółki w panelu bocznym lub wybierz z listy popularnych.
""")

#Panel Boczny - konfiguracja
st.sidebar.header("Ustawienia Macierzy")

#Lista popularnych instrumentow
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

#Pole na własne instrumenty
st.sidebar.markdown("---")
manual_tickers_input = st.sidebar.text_area(
    "Lub wpisz własne (oddzielone przecinkiem):",
    placeholder="np. PEP, KO, DNP.WA, ALR.WA",
    help="Wpisz tutaj dowolne symbole z Yahoo Finance oddzielone przecinkami."
)

# Logika łączenia list
# Rozbijanie wpisanego tekstu na listę, usuwamy spacje i zamieniamy na wielkie litery
manual_tickers = []
if manual_tickers_input:
    manual_tickers = [x.strip().upper() for x in manual_tickers_input.split(",") if x.strip()]

#Laczenie obu list i usuwanie duplikatów
final_ticker_list = list(set(selected_from_list + manual_tickers))

st.sidebar.markdown(f"**Wybrano łącznie:** {len(final_ticker_list)} aktywów")

#Wybor okresu
period = st.sidebar.selectbox(
    "Okres danych:",
    options=["3mo", "6mo", "1y", "2y", "5y"],
    index=2
)

#Zabezpieczenie (min 2 spolki zeby mozliwe bylo zrobienie macierzy)
if len(final_ticker_list) < 2:
    st.info("Wybierz lub wpisz przynajmniej dwie spółki w panelu bocznym, aby zobaczyć korelację.")
    st.stop()

#Pobieranie i przetwarzanie danych
if st.button("Oblicz Korelację"):
    fetcher = StockData()
    combined_df = pd.DataFrame()
    progress_bar = st.progress(0)

    with st.spinner("Pobieranie danych..."):
        for i, ticker in enumerate(final_ticker_list):
            #Pobieranie danych
            df = fetcher.get_data(ticker, period=period, interval="1d")

            if not df.empty and "Close" in df.columns:
                #Obliczanie dziennych zwrotów procentowych
                combined_df[ticker] = df["Close"].pct_change()

            #Aktualizacja paska postępu
            progress_bar.progress((i + 1) / len(final_ticker_list))

    #Usuwanie brakow w wierszach (NaN po pct_change) (np swieto w jednym kraju przez co gielda jest zamknieta)
    combined_df = combined_df.dropna()

    if combined_df.empty:
        st.error("Nie udało się pobrać wystarczających danych. Sprawdź, czy wpisane symbole są poprawne.")
    else:
        #Obliczanie Korelacji (metoda Pearsona)
        corr_matrix = combined_df.corr()

        #Wizualizacja (Plotly)
        fig = px.imshow(
            corr_matrix,
            text_auto=".2f", #Wartosci liczbowe na kafelkach
            aspect="auto",
            color_continuous_scale="RdBu_r",  # Czerwony (1.0) - Niebieski (-1.0)
            zmin=-1, zmax=1, #Sztywne ramy od -1 do 1
            title=f"Korelacja portfela ({period})"
        )

        fig.update_layout(
            height=700,
            xaxis_title=None,
            yaxis_title=None
        )

        st.plotly_chart(fig, use_container_width=True)

        #Wnioski
        st.subheader("Wnioski:")

        #Najsilniejsza para
        c = corr_matrix.abs() #Wartosc bezwgzgledna (sama sila zwiazku)
        #Wypełnienie przekątnej zerami, żeby nie znajdowało korelacji 1.0 samej ze sobą
        for col in c.columns:
            c.loc[col, col] = 0

        s = c.unstack() #Zamiana macierzy w liste par
        so = s.sort_values(kind="quicksort", ascending=False)

        #Wyswietlanie topowego wyniku
        if not so.empty:
            top_pair = so.index[0] #Nazwy najlepszej pary
            top_val = corr_matrix.loc[top_pair[0], top_pair[1]]  #Pobieranie oryginalnej wartości (+/-)

            st.info(f"Najsilniejsze powiązanie: **{top_pair[0]}** i **{top_pair[1]}** (Korelacja: {top_val:.2f}).")

            if top_val > 0.8:
                st.warning(
                    "**Wysokie ryzyko koncentracji!** Te dwa aktywa są od siebie bardzo zależne. Jeśli jedno spadnie, drugie prawdopodobnie też.")
            elif top_val < 0.2 and top_val > -0.2:
                st.success("Znaleziono aktywa nieskorelowane. To dobrze wpływa na bezpieczeństwo portfela.")
#Disclaimer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: small;'>
        <b>Nota prawna:</b> Aplikacja służy wyłącznie celom edukacyjnym i informacyjnym. 
        Prezentowane dane nie stanowią porady inwestycyjnej ani rekomendacji w rozumieniu przepisów prawa. 
        Pamiętaj, że inwestowanie wiąże się z ryzykiem utraty kapitału.
    </div>
    """,
    unsafe_allow_html=True
)