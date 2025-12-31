import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.data import StockData
from src.analyzer import StockAnalyzer

st.set_page_config(page_title="Smart Portfolio Studio", layout="wide")
st.title("📊 Smart Portfolio Studio - Analiza Akcji")

#Panel boczny
st.sidebar.header("Opcje użytkownika")

#Przycisk do odświeżania danych
if st.sidebar.button("🔄 Odśwież dane",
                     help="Wymusza pobranie nowych danych z Yahoo Finance, ignorując zapisane pliki (cache)."):
    st.cache_data.clear()
    st.rerun()

period = st.sidebar.selectbox(
    "Wybierz okres analizy",
    options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y"],
    index=2,
    help="Określa, z jakiego okresu wstecz pobieramy dane. Np. '1y' to ostatni rok."
)

interval = st.sidebar.selectbox(
    "Wybierz interwał",
    options=["1d", "1wk", "1mo"],
    index=0,
    help="Jeden punkt na wykresie to: '1d' = jeden dzień, '1wk' = jeden tydzień. Dla długich okresów (np. 5 lat) warto wybrać '1wk'."
)

#Inteligentny Benchmark
st.sidebar.markdown("### 🆚 Porównanie (Benchmark)")

benchmarks_dict = {
    "Brak": None,
    "S&P 500 (USA)": "SPY",
    "NASDAQ (Tech)": "QQQ",
    "WIG20 (Polska)": "WIG20.PL",
    "DAX (Niemcy)": "^GDAXI",
    "Złoto": "GLD",
    "Bitcoin": "BTC-USD",
    "Inny (wpisz ręcznie)": "CUSTOM"
}

selected_bench_label = st.sidebar.selectbox(
    "Wybierz punkt odniesienia:",
    options=list(benchmarks_dict.keys()),
    index=0,
    help="Porównaj wynik wybranej spółki z indeksem giełdowym. Pozwala ocenić, czy spółka radzi sobie lepiej od rynku."
)

benchmark_ticker = benchmarks_dict[selected_bench_label]

if benchmark_ticker == "CUSTOM":
    benchmark_ticker = st.sidebar.text_input(
        "Wpisz symbol benchmarku:",
        value="MSFT",
        help="Wpisz symbol zgodny z Yahoo Finance (np. 'KGH.WA' dla KGHM)."
    ).upper().strip()

#Wybór Spółki
st.sidebar.header("🔍 Wybór Aktywa")

default_tickers = ["AAPL", "NVDA", "MSFT", "TSLA", "BTC-USD", "ETH-USD", "CDPROJEKT.WA", "KGH.WA", "DNP.WA"]
stock_list = default_tickers

try:
    stocks_df = pd.read_csv("stocks_list.csv")
    if "ticker" in stocks_df.columns:
        stock_list = stocks_df["ticker"].tolist()
except FileNotFoundError:
    pass

selected_ticker_from_list = st.sidebar.selectbox(
    "Wybierz z listy:",
    options=stock_list,
    index=0
)

custom_ticker = st.sidebar.text_input(
    "Lub wpisz symbol ręcznie:",
    placeholder="np. BTC-USD, PKO.WA, GLD",
    help="Wpisz ticker. Dla Polski dodaj końcówkę .WA (np. PKO.WA, CDR.WA). Krypto: BTC-USD."
).upper().strip()

ticker = custom_ticker if custom_ticker else selected_ticker_from_list

st.sidebar.markdown(f"**Wybrano:** `{ticker}`")

#Pobranie danych
fetcher = StockData()
df = fetcher.get_data(ticker, period=period, interval=interval)
ticker_info = fetcher.get_ticker_info(ticker)
currency = ticker_info.get("currency", "USD")

#Eksport danych
#Umieszczamy to TUTAJ, bo dopiero teraz mamy zmienną 'df' i 'ticker'
if not df.empty:
    st.sidebar.markdown("---")
    st.sidebar.write("📥 **Eksport danych**")


    @st.cache_data
    def convert_df(df_to_convert):
        return df_to_convert.to_csv().encode('utf-8')


    csv = convert_df(df)

    st.sidebar.download_button(
        label="Pobierz plik CSV",
        data=csv,
        file_name=f"{ticker}_dane.csv",
        mime="text/csv",
        help="Pobierz tabelę z cenami historycznymi do pliku Excel/CSV."
    )

#Stopka Autora
st.sidebar.markdown("---")
st.sidebar.markdown("### Autor")
st.sidebar.info("**Adam Woźniak**")
st.sidebar.markdown("[GitHub](https://github.com/wozniakadam71) | [LinkedIn](www.linkedin.com/in/adam-woźniak-b59473380)")

#Główny Panel
st.markdown(f"### 🏢 {ticker_info.get('name', ticker)}")

if ticker_info.get('website'):
    st.markdown(
        f"[{ticker_info['website']}]({ticker_info['website']}) • {ticker_info.get('sector', '')} • {ticker_info.get('industry', '')}")

fund_col1, fund_col2, fund_col3, fund_col4 = st.columns(4)

#Kapitalizacja
mcap = ticker_info.get('market_cap')
if mcap:
    if mcap > 1e9:
        mcap_str = f"{mcap / 1e9:.2f} mld {currency}"
    else:
        mcap_str = f"{mcap / 1e6:.2f} mln {currency}"
    fund_col1.metric("Kapitalizacja", mcap_str,
                     help="Łączna wartość rynkowa wszystkich akcji spółki. (Liczba akcji × Cena akcji).")
else:
    fund_col1.metric("Kapitalizacja", "---")

#Cena / Zysk (P/E)
pe = ticker_info.get('pe_ratio')
fund_col2.metric("Cena / Zysk (P/E)", f"{pe:.2f}" if pe else "---",
                 help="Price to Earnings. Mówi, ile dolarów/złotych inwestorzy płacą za 1 jednostkę zysku. Wysokie P/E (>25) może oznaczać, że spółka jest 'droga' lub dynamicznie rośnie. Niskie (<15) może oznaczać okazję.")

#Dywidenda
div = ticker_info.get('dividend_yield')
div_str = "---"
if div is not None:
    if div > 0.5:
        div_str = f"{div:.2f}%"
    else:
        div_str = f"{div * 100:.2f}%"
fund_col3.metric("Dywidenda", div_str,
                 help="Roczna stopa zwrotu wypłacana akcjonariuszom w gotówce. Np. 5% oznacza, że za zainwestowane 100 zł otrzymasz 5 zł rocznie (brutto).")

#P/E Prognozowane
f_pe = ticker_info.get('forward_pe')
fund_col4.metric("Prognoza P/E", f"{f_pe:.2f}" if f_pe else "---",
                 help="Wskaźnik Cena/Zysk obliczony na podstawie przewidywanych zysków w przyszłym roku.")

st.markdown("---")

if df.empty:
    st.warning("Brak danych dla wybranej spółki.")
    st.stop()

#Analiza
analyzer = StockAnalyzer(df)
analyzer.calculate_returns()
analyzer.calculate_volatility()
analyzer.calculate_ema(short_window=12, long_window=26)
analyzer.calculate_macd()
analyzer.calculate_rsi()

#Wyświetlanie statystyk
st.subheader(f"Statystyki dla {ticker}")
stats = analyzer.basic_stats()

col1, col2, col3, col4 = st.columns(4)
col1.metric(f"Średnia cena ({currency})", f"{float(stats['średnia cena']):.2f}",
            help="Średnia arytmetyczna ceny zamknięcia z wybranego okresu.")
col2.metric("Mediana ceny", f"{float(stats['mediana ceny']):.2f}",
            help="Środkowa wartość ceny. Często lepsza miara niż średnia, bo odporna na pojedyncze skoki cen.")
col3.metric("RSI (14)", f"{analyzer.rsi.iloc[-1]:.2f}",
            help="Relative Strength Index. Mierzy prędkość i zmiany cen. \n\n• Powyżej 70: 'Wykupienie' (możliwy spadek).\n• Poniżej 30: 'Wyprzedanie' (możliwy wzrost).")
col4.metric("Zmienność", f"{analyzer.volatility:.4f}",
            help="Odchylenie standardowe zwrotów. Im wyższa liczba, tym bardziej 'szalony' jest kurs (duże ryzyko, ale i szansa na duży zysk).")

#Wskaźniki Ryzyka
try:
    risk = analyzer.get_risk_metrics()

    st.markdown("##### 📉 Wskaźniki Ryzyka")
    r_col1, r_col2 = st.columns(2)

    r_col1.metric(
        "Sharpe Ratio (Roczny)",
        f"{risk['sharpe_ratio']:.2f}",
        help="Miara opłacalności inwestycji w stosunku do ryzyka. \n• > 1: Dobrze \n• > 2: Bardzo dobrze \n• > 3: Wybitnie. \nJeśli ujemne, inwestycja nie rekompensowała ryzyka."
    )

    r_col2.metric(
        "Max Drawdown (Max Spadek)",
        f"{risk['max_drawdown'] * 100:.2f}%",
        help="Maksymalny procentowy spadek wartości od szczytu do dołka w wybranym okresie. Mówi o tym, jak bardzo mogłeś 'oberwać' w najgorszym momencie."
    )
except AttributeError:
    pass

#Wykres cen z EMA
fig_price = go.Figure()

#Główna cena
fig_price.add_trace(go.Scatter(
    x=df.index,
    y=df["Close"],
    mode="lines",
    name="Cena zamknięcia",
    line=dict(width=1, color='gray')
))

if "EMA_short" in df.columns and "EMA_long" in df.columns:
    #EMA 12 (Szybka)
    fig_price.add_trace(go.Scatter(
        x=df.index,
        y=df["EMA_short"],
        mode="lines",
        name="EMA 12 (Szybka)",
        line=dict(dash='solid', color='orange', width=2)
    ))

    #EMA 26 (Wolna)
    fig_price.add_trace(go.Scatter(
        x=df.index,
        y=df["EMA_long"],
        mode="lines",
        name="EMA 26 (Wolna)",
        line=dict(dash='solid', color='purple', width=2)
    ))

fig_price.update_layout(title=f"Cena akcji {ticker} + Średnie EMA", xaxis_title="Data", yaxis_title="Cena")
st.plotly_chart(fig_price, use_container_width=True)

with st.expander("ℹ️ Co to są linie EMA 12 i 26? (Kliknij, aby rozwinąć)"):
    st.markdown("""
    **EMA (Exponential Moving Average)** to średnia, która nadaje większą wagę najświeższym cenom. Reaguje szybciej niż zwykła średnia.

    * 🟠 **EMA 12 (Pomarańczowa):** Krótkoterminowy trend. Trzyma się blisko ceny.
    * 🟣 **EMA 26 (Fioletowa):** Średnioterminowy trend. Filtruje "szum" i pokazuje ogólny kierunek.

    **Jak tego używać?**
    1.  **Określanie trendu:** Jeśli **Cena** jest nad obiema liniami -> Silny trend wzrostowy 📈.
    2.  **Wsparcie/Opór:** Często cena "odbija się" od linii EMA 26 (fioletowej) podczas korekt.
    3.  **Przecięcia:** Gdy Pomarańczowa (12) przecina Fioletową (26) od dołu, jest to sygnał wzrostowy (często zwiastuje zmianę trendu).
    """)

#Sekcja Porównania
if benchmark_ticker:
    st.markdown("---")
    st.subheader(f"🆚 Porównanie: {ticker} vs {benchmark_ticker}")

    bench_df = fetcher.get_data(benchmark_ticker, period=period, interval=interval)

    if not bench_df.empty and len(bench_df) > 0:
        #Normalizacja
        norm_main = df["Close"] / df["Close"].iloc[0] * 100
        norm_bench = bench_df["Close"] / bench_df["Close"].iloc[0] * 100

        fig_compare = go.Figure()
        fig_compare.add_trace(go.Scatter(x=df.index, y=norm_main, mode="lines", name=ticker))
        fig_compare.add_trace(
            go.Scatter(x=bench_df.index, y=norm_bench, mode="lines", name=benchmark_ticker, line=dict(dash='dash')))

        fig_compare.update_layout(
            title="Porównanie stopy zwrotu (Start = 100)",
            xaxis_title="Data",
            yaxis_title="Wartość znormalizowana",
            hovermode="x unified"
        )
        st.plotly_chart(fig_compare, use_container_width=True)
    else:
        st.warning(f"Nie udało się pobrać danych dla {benchmark_ticker}. Może to błędny symbol?")

#Wykres MACD
fig_macd = go.Figure()
if "MACD" in df.columns and "MACD_signal" in df.columns:
    #Linia MACD (Szybka)
    fig_macd.add_trace(go.Scatter(
        x=df.index,
        y=df["MACD"],
        mode="lines",
        name="MACD (Szybka)",
        line=dict(color="blue", width=2)
    ))

    #Linia Sygnału (Wolna)
    fig_macd.add_trace(go.Scatter(
        x=df.index,
        y=df["MACD_signal"],
        mode="lines",
        name="Sygnał (Wolna)",
        line=dict(color="red", width=2)
    ))

    fig_macd.update_layout(title=f"MACD dla {ticker}", xaxis_title="Data", yaxis_title="Wartość")
    st.plotly_chart(fig_macd, use_container_width=True)

    with st.expander("ℹ️ Jak czytać sygnały MACD? (Kliknij, aby rozwinąć)"):
        st.markdown("""
        **Legenda:**
        * 🔵 **Linia Niebieska (MACD):** Pokazuje aktualny impet ceny. Reaguje szybko.
        * 🔴 **Linia Czerwona (Sygnał):** To średnia z linii niebieskiej. Reaguje wolniej.

        **Sygnały transakcyjne:**
        1.  🚀 **KUPUJ (Golden Cross):** Gdy **Niebieska** przecina Czerwoną od dołu i idzie w górę. Oznacza to, że cena nabiera rozpędu.
        2.  🔻 **SPRZEDAWAJ (Death Cross):** Gdy **Niebieska** przecina Czerwoną od góry i spada w dół. Oznacza to, że wzrosty słabną.
        """)

#Wykres RSI
fig_rsi = go.Figure()
if "RSI" in df.columns:
    fig_rsi.add_trace(go.Scatter(x=df.index, y=df["RSI"], mode="lines", name="RSI"))

    #Poziome linie
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")

    fig_rsi.update_layout(title=f"RSI dla {ticker}", xaxis_title="Data", yaxis_title="RSI")
    st.plotly_chart(fig_rsi, use_container_width=True)

#Symulator Inwestycji (Backtesting)
st.markdown("---")
st.subheader("💰 Symulator Inwestycji")

from src.backtester import SimpleBacktester

col_sim1, col_sim2 = st.columns([1, 2])

with col_sim1:
    investment = st.number_input(
        f"Kwota inwestycji ({currency}):",
        min_value=100,
        value=10000,
        step=100,
        help="Kwota, którą wirtualnie inwestujesz na początku wybranego okresu."
    )
    run_sim = st.button("Oblicz zysk")

with col_sim2:
    if run_sim:
        if len(df) < 30:
            st.error(f"⚠️ Za mało danych do analizy wskaźnikowej (pobrano {len(df)} wierszy). Zwiększ 'Okres analizy'.")
        else:
            backtester = SimpleBacktester(df, initial_capital=investment)
            res = backtester.run_strategy()

            if not res:
                start_price = df["Close"].iloc[0]
                end_price = df["Close"].iloc[-1]
                shares = investment / start_price
                final_val = shares * end_price
                profit = final_val - investment
                roi = (profit / investment) * 100

                res = {
                    "final_value": final_val,
                    "profit": profit,
                    "roi": roi,
                    "shares": shares,
                    "start_date": df.index[0],
                    "start_price": start_price
                }
                st.warning(
                    "⚠️ Brak sygnałów technicznych (EMA). Pokazuję wynik strategii 'Kup i Trzymaj' (Buy & Hold).")

            color = "green" if res["profit"] >= 0 else "red"
            m1, m2, m3 = st.columns(3)
            m1.metric("Wartość końcowa", f"{res['final_value']:.2f} {currency}")
            m2.metric("Zysk/Strata", f"{res['profit']:.2f} {currency}", delta_color="normal")
            m3.metric("ROI", f"{res['roi']:.2f}%", delta=f"{res['roi']:.2f}%",
                      help="Return On Investment. Zwrot z inwestycji w procentach.")

            st.info(
                f"Gdybyś kupił **{res['shares']:.4f}** akcji w dniu **{res['start_date'].strftime('%Y-%m-%d')}** "
                f"po cenie **{res['start_price']:.2f} {currency}**, dzisiaj miałbyś powyższą kwotę."
            )