import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf

# Import wlasnych modolow zapisanych w innych plikach
from src.data import StockData
from src.analyzer import StockAnalyzer
from src.database import WatchlistDB
from src.backtester import SimpleBacktester

# Setup glownej strony
st.set_page_config(page_title="Analiza Akcji", layout="wide")
st.title("📊 Smart Portfolio Studio - Analiza Akcji")

# Panel boczny
st.sidebar.header("⚙️ Opcje użytkownika")

if st.sidebar.button("Odśwież dane", help="Wymusza pobranie nowych danych z Yahoo Finance."):
    st.cache_data.clear()
    st.rerun()

period = st.sidebar.selectbox("Wybierz okres analizy", options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y"], index=2)
interval = st.sidebar.selectbox("Wybierz interwał", options=["1d", "1wk", "1mo"], index=0)

# --- WYBÓR AKTYWA ---
st.sidebar.header("Wybór Aktywa")
db = WatchlistDB()
saved_tickers = db.get_tickers()

source_option = st.sidebar.radio("Źródło listy:", ["⭐ Moje Ulubione", "Predefiniowane"], horizontal=True)

if source_option == "⭐ Moje Ulubione":
    current_list = saved_tickers if saved_tickers else ["AAPL", "NVDA", "BTC-USD"]
else:
    current_list = ["AAPL", "NVDA", "MSFT", "TSLA", "BTC-USD", "ETH-USD", "CDPROJEKT.WA", "KGH.WA", "DNP.WA"]

selected_ticker_from_list = st.sidebar.selectbox("Wybierz spółkę:", options=current_list, index=0)
custom_ticker = st.sidebar.text_input("Lub wpisz symbol ręcznie:", placeholder="np. PLTR, XTB.WA").upper().strip()
ticker = custom_ticker if custom_ticker else selected_ticker_from_list

# Przyciski bazy
col_add, col_del = st.sidebar.columns(2)
with col_add:
    if st.button("⭐ Dodaj"):
        db.add_ticker(ticker)
        st.success(f"Dodano {ticker}!")
        st.rerun()

with col_del:
    if st.button("🗑️ Usuń"):
        if ticker in saved_tickers:
            db.remove_ticker(ticker)
            st.warning(f"Usunięto {ticker}!")
            st.rerun()
        else:
            st.error("Nie ma na liście.")

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Wybrano:** `{ticker}`")

# Pobieranie danych
fetcher = StockData()
df = fetcher.get_data(ticker, period=period, interval=interval)
ticker_info = fetcher.get_ticker_info(ticker)
currency = ticker_info.get("currency", "USD")

# Benchmark
st.sidebar.markdown("### Porównanie (Benchmark)")
benchmarks_dict = {
    "Brak": None, "S&P 500 (USA)": "SPY", "NASDAQ (Tech)": "QQQ",
    "WIG20 (Polska)": "WIG20.WA", "DAX (Niemcy)": "^GDAXI",
    "Złoto": "GLD", "Bitcoin": "BTC-USD", "Inny (wpisz ręcznie)": "CUSTOM"
}
selected_bench_label = st.sidebar.selectbox("Wybierz punkt odniesienia:", options=list(benchmarks_dict.keys()), index=0)
benchmark_ticker = benchmarks_dict[selected_bench_label]

if benchmark_ticker == "CUSTOM":
    benchmark_ticker = st.sidebar.text_input("Wpisz symbol benchmarku:", value="MSFT").upper().strip()

# Stopka Autora
st.sidebar.markdown("---")
st.sidebar.info("**Adam Woźniak**")

# --- GŁÓWNY PANEL ---
st.markdown(f"### {ticker_info.get('name', ticker)}")
if ticker_info.get('website'):
    st.markdown(
        f"[{ticker_info['website']}]({ticker_info['website']}) • {ticker_info.get('sector', '')} • {ticker_info.get('industry', '')}")

# 1. FUNDAMENTY W KAFELKACH
st.markdown("#### 🏢 Dane Fundamentalne")
fund_col1, fund_col2, fund_col3, fund_col4 = st.columns(4)

with fund_col1:
    with st.container(border=True):
        mcap = ticker_info.get('market_cap')
        mcap_str = f"{mcap / 1e9:.2f} mld {currency}" if mcap and mcap > 1e9 else f"{mcap / 1e6:.2f} mln {currency}" if mcap else "---"
        st.metric("Kapitalizacja", mcap_str)

with fund_col2:
    with st.container(border=True):
        pe = ticker_info.get('pe_ratio')
        st.metric("Cena / Zysk (P/E)", f"{pe:.2f}" if pe else "---")

with fund_col3:
    with st.container(border=True):
        div = ticker_info.get('dividend_yield')
        div_str = f"{div:.2f}%" if div and div > 0.5 else f"{div * 100:.2f}%" if div else "---"
        st.metric("Dywidenda", div_str)

with fund_col4:
    with st.container(border=True):
        f_pe = ticker_info.get('forward_pe')
        st.metric("Prognoza P/E", f"{f_pe:.2f}" if f_pe else "---")

st.markdown("---")

if df.empty:
    st.warning("Brak danych dla wybranej spółki.")
    st.stop()

# Analiza techniczna
analyzer = StockAnalyzer(df)
analyzer.calculate_returns()
analyzer.calculate_volatility()
analyzer.calculate_ema(short_window=12, long_window=26)
analyzer.calculate_macd()
analyzer.calculate_rsi()

# 2. STATYSTYKI W KAFELKACH
st.subheader("📈 Statystyki Techniczne")
stats = analyzer.basic_stats()

c1, c2, c3, c4 = st.columns(4)
with c1:
    with st.container(border=True):
        st.metric(f"Średnia cena", f"{float(stats['średnia cena']):.2f} {currency}")
with c2:
    with st.container(border=True):
        st.metric("Mediana ceny", f"{float(stats['mediana ceny']):.2f} {currency}")
with c3:
    with st.container(border=True):
        st.metric("RSI (14)", f"{analyzer.rsi.iloc[-1]:.2f}")
with c4:
    with st.container(border=True):
        st.metric("Zmienność", f"{analyzer.volatility:.4f}")

# --- SEKCJA WERDYKTU AI ---
st.markdown("---")
st.subheader("🤖 Werdykt Algorytmu (Analiza Techniczna)")


def get_technical_score(df_tech):
    score = 0
    reasons = []
    last_rsi = df_tech['RSI'].iloc[-1]
    if last_rsi < 30:
        score += 2; reasons.append(f"🟢 RSI ({last_rsi:.1f}) wskazuje wyprzedanie (okazja?)")
    elif last_rsi > 70:
        score -= 2; reasons.append(f"🔴 RSI ({last_rsi:.1f}) wskazuje wykupienie")
    else:
        reasons.append(f"⚪ RSI ({last_rsi:.1f}) jest neutralne")

    if 'EMA_long' in df_tech.columns:
        if df_tech['Close'].iloc[-1] > df_tech['EMA_long'].iloc[-1]:
            score += 3; reasons.append("🟢 Cena powyżej długoterminowej średniej")
        else:
            score -= 3; reasons.append("🔴 Cena poniżej długoterminowej średniej")

    if 'MACD' in df_tech.columns and 'MACD_signal' in df_tech.columns:
        if df_tech['MACD'].iloc[-1] > df_tech['MACD_signal'].iloc[-1]:
            score += 2; reasons.append("🟢 MACD przebiło linię sygnału od dołu")
        elif df_tech['MACD'].iloc[-1] < df_tech['MACD_signal'].iloc[-1]:
            score -= 2; reasons.append("🔴 MACD poniżej linii sygnału")

    return score, reasons


if len(df) > 30:
    with st.container(border=True):
        total_score, rationale = get_technical_score(df)

        if total_score >= 4:
            verdict, color = "MOCNE KUPUJ 🚀", "#2E8B57"
        elif total_score >= 1:
            verdict, color = "KUPUJ ↗️", "#00CC96"
        elif total_score > -1:
            verdict, color = "NEUTRALNIE 😐", "#AB63FA"
        elif total_score > -4:
            verdict, color = "SPRZEDAWAJ ↘️", "#FFA15A"
        else:
            verdict, color = "MOCNE SPRZEDAWAJ 🔻", "#EF553B"

        v_col1, v_col2 = st.columns([1, 1])
        with v_col1:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number", value=total_score, domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Siła Sygnału", 'font': {'size': 20}},
                gauge={'axis': {'range': [-7, 7]}, 'bar': {'color': "black", 'thickness': 0.3},
                       'steps': [{'range': [-7, -3], 'color': '#EF553B'}, {'range': [-3, -1], 'color': '#FFA15A'},
                                 {'range': [-1, 1], 'color': '#AB63FA'}, {'range': [1, 3], 'color': '#00CC96'},
                                 {'range': [3, 7], 'color': '#2E8B57'}]}
            ))
            fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True, key="gauge_ai")

        with v_col2:
            st.markdown(f"### Decyzja: <span style='color:{color}'>{verdict}</span>", unsafe_allow_html=True)
            st.write("**Dlaczego taka ocena?**")
            for r in rationale: st.caption(f"{r}")
else:
    st.warning("⚠️ Za mało danych historycznych, aby algorytm mógł podjąć decyzję.")

# --- SEKCJA FUNDAMENTALNA - RADAR ---
st.markdown("---")
st.subheader("💎 Radar Fundamentalny")

try:
    info = ticker_info
    if 'trailingPE' in info or 'totalRevenue' in info:
        pe = info.get('trailingPE', 50) or 50
        score_value = max(0, min(100, 100 - (pe * 1.5)))
        margin = info.get('profitMargins', 0) or 0
        score_profit = 90 if margin > 0.2 else max(0, min(100, margin * 100 * 2))
        roe = info.get('returnOnEquity', 0) or 0
        score_efficiency = max(0, min(100, roe * 100 * 2))
        debt_eq = info.get('debtToEquity', 100) or 100
        score_health = max(0, min(100, 100 - (debt_eq / 2)))
        current_p = info.get('currentPrice', 1)
        target_p = info.get('targetMeanPrice', current_p)
        score_growth = max(0, min(100,
                                  50 + (((target_p - current_p) / current_p) * 100))) if target_p and current_p else 50

        with st.container(border=True):
            col_radar, col_desc = st.columns([1, 1])
            with col_radar:
                categories = ['Wycena (Taniość)', 'Zyskowność', 'Efektywność (ROE)', 'Bezpieczeństwo',
                              'Potencjał Wzrostu']
                values = [score_value, score_profit, score_efficiency, score_health, score_growth]
                values += [values[0]];
                categories += [categories[0]]

                fig = go.Figure(
                    go.Scatterpolar(r=values, theta=categories, fill='toself', name=ticker, line=dict(color='#00CC96'),
                                    fillcolor='rgba(0, 204, 150, 0.2)'))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False,
                                  margin=dict(l=40, r=40, t=20, b=20), height=300)
                st.plotly_chart(fig, use_container_width=True, key="radar_chart")

            with col_desc:
                st.markdown("#### 🔍 Szybka Diagnoza")
                st.write(f"**🏷️ P/E (Cena/Zysk):** {pe:.2f}" if pe != 50 else "**🏷️ P/E (Cena/Zysk):** ?")
                if pe < 15:
                    st.caption("✅ Spółka wyceniana atrakcyjnie.")
                elif pe > 40:
                    st.caption("⚠️ Spółka jest droga.")
                st.write(f"**💰 Marża Netto:** {margin * 100:.1f}%")
                if margin > 0.2: st.caption("🔥 To maszynka do robienia pieniędzy.")
                st.write(f"**🛡️ Zadłużenie/Kapitał:** {debt_eq:.2f}%")
                avg_score = sum(values[:-1]) / 5
                st.markdown("---")
                st.metric("Ogólna Ocena Fundamentów", f"{avg_score:.0f}/100")
except Exception as e:
    pass

# --- WYKRESY CENOWE ---
st.markdown("---")
st.subheader(f"🕯️ Wykres Cenowy: {ticker}")

fig_price = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_width=[0.2, 0.7])
fig_price.add_trace(
    go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Cena'), row=1,
    col=1)

if "EMA_short" in df.columns and "EMA_long" in df.columns:
    fig_price.add_trace(
        go.Scatter(x=df.index, y=df["EMA_short"], mode="lines", name="EMA 12", line=dict(color='orange', width=1.5)),
        row=1, col=1)
    fig_price.add_trace(
        go.Scatter(x=df.index, y=df["EMA_long"], mode="lines", name="EMA 26", line=dict(color='purple', width=1.5)),
        row=1, col=1)

colors = ['#00CC96' if row['Open'] - row['Close'] >= 0 else '#EF553B' for index, row in df.iterrows()]
fig_price.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Wolumen', marker_color=colors, opacity=0.5), row=2, col=1)

fig_price.update_layout(xaxis_rangeslider_visible=False, hovermode='x unified', height=600,
                        margin=dict(l=20, r=20, t=40, b=20),
                        xaxis=dict(rangebreaks=[dict(bounds=["sat", "mon"])]) if "USD" not in ticker else None)

with st.container(border=True):
    st.plotly_chart(fig_price, use_container_width=True, key="main_price_chart")

with st.expander("ℹ️ Jak czytać ten wykres? (Świece + EMA)"):
    st.markdown("""
    * **Świece (Candles):** Pokazują walkę popytu i podaży. Zielona = cena wzrosła, Czerwona = spadła. Knoty pokazują max/min cenę w danym okresie.
    * **Słupki na dole (Wolumen):** Jak dużo akcji zmieniło właściciela. Wysoki słupek przy zmianie ceny potwierdza siłę ruchu.
    * **EMA 12 (Pomarańczowa) i 26 (Fioletowa):** Średnie ruchome. Gdy cena jest nad nimi -> Trend wzrostowy. Przecięcie linii to sygnał transakcyjny.
    """)

# --- PORÓWNANIE Z BENCHMARKIEM ---
if benchmark_ticker:
    st.markdown("---")
    st.subheader(f"⚖️ Porównanie: {ticker} vs {benchmark_ticker}")

    bench_df = fetcher.get_data(benchmark_ticker, period=period, interval=interval)

    if not bench_df.empty and len(bench_df) > 0:
        with st.container(border=True):
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
                hovermode="x unified",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_compare, use_container_width=True, key="compare_chart")
    else:
        st.warning(f"Nie udało się pobrać danych dla {benchmark_ticker}. Może to błędny symbol?")

# --- WYKRES MACD ---
if "MACD" in df.columns and "MACD_signal" in df.columns:
    st.markdown("---")
    st.subheader("📊 Wskaźnik MACD")
    with st.container(border=True):
        fig_macd = go.Figure()
        fig_macd.add_trace(
            go.Scatter(x=df.index, y=df["MACD"], mode="lines", name="MACD (Szybka)", line=dict(color="blue", width=2)))
        fig_macd.add_trace(go.Scatter(x=df.index, y=df["MACD_signal"], mode="lines", name="Sygnał (Wolna)",
                                      line=dict(color="red", width=2)))

        fig_macd.update_layout(title=f"MACD dla {ticker}", hovermode="x unified", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_macd, use_container_width=True, key="macd_chart")

        with st.expander("ℹ️ Jak czytać sygnały MACD? (Kliknij, aby rozwinąć)"):
            st.markdown("""
            **Legenda:**
            * 🔵 **Linia Niebieska (MACD):** Pokazuje aktualny impet ceny. Reaguje szybko.
            * 🔴 **Linia Czerwona (Sygnał):** To średnia z linii niebieskiej. Reaguje wolniej.

            **Sygnały transakcyjne:**
            1.   **KUPUJ (Golden Cross):** Gdy **Niebieska** przecina Czerwoną od dołu i idzie w górę. Oznacza to, że cena nabiera rozpędu.
            2.   **SPRZEDAWAJ (Death Cross):** Gdy **Niebieska** przecina Czerwoną od góry i spada w dół. Oznacza to, że wzrosty słabną.
            """)

# --- WYKRES RSI ---
if "RSI" in df.columns:
    st.markdown("---")
    st.subheader("📉 Wskaźnik RSI")
    with st.container(border=True):
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df["RSI"], mode="lines", name="RSI"))

        # Poziome linie
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Wykupienie (70)")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Wyprzedanie (30)")

        fig_rsi.update_layout(title=f"RSI dla {ticker}", hovermode="x unified", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_rsi, use_container_width=True, key="rsi_chart")

# SYMULATOR INWESTYCJI
st.markdown("---")
st.subheader("🕹️ Symulator Inwestycji")

with st.container(border=True):
    col_sim1, col_sim2 = st.columns([1, 2])
    with col_sim1:
        investment = st.number_input(f"Kwota inwestycji ({currency}):", min_value=100, value=10000, step=100)
        run_sim = st.button("Oblicz zysk")

    with col_sim2:
        if run_sim:
            if len(df) < 30:
                st.error("Za mało danych do symulacji.")
            else:
                backtester = SimpleBacktester(df, initial_capital=investment)
                res = backtester.run_strategy()
                if not res:
                    start_price, end_price = df["Close"].iloc[0], df["Close"].iloc[-1]
                    shares = investment / start_price
                    res = {
                        "final_value": shares * end_price,
                        "profit": (shares * end_price) - investment,
                        "roi": (((shares * end_price) - investment) / investment) * 100,
                        "shares": shares,
                        "start_date": df.index[0],
                        "start_price": start_price
                    }
                    st.warning("Brak sygnałów technicznych. Pokazuję wynik strategii 'Kup i Trzymaj'.")

                m1, m2, m3 = st.columns(3)
                m1.metric("Wartość końcowa", f"{res['final_value']:.2f} {currency}")
                m2.metric("Zysk/Strata", f"{res['profit']:.2f} {currency}", delta_color="normal")
                m3.metric("ROI", f"{res['roi']:.2f}%", delta=f"{res['roi']:.2f}%")

# NEWSY
st.markdown("---")
clean_ticker = ticker.replace(".WA", "")
news_url = f"https://www.bankier.pl/gielda/notowania/akcje/{clean_ticker}/wiadomosci" if ticker.endswith(
    ".WA") else f"https://finance.yahoo.com/quote/{ticker}/news"
source_name = "Bankier.pl" if ticker.endswith(".WA") else "Yahoo Finance"

with st.container(border=True):
    st.info(f"Najnowsze wiadomości dla **{ticker}** znajdziesz w serwisie **{source_name}**.")
    st.link_button(f"🔗 Zobacz najnowsze newsy na {source_name}", news_url)