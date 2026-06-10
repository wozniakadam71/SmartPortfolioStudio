import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime, timedelta
import re
from io import BytesIO
from src.database import PortfolioDB
from src.data import get_exchange_rate, get_historical_price

st.set_page_config(page_title="Mój Portfel", layout="wide")
st.title("💼 Mój Portfel Inwestycyjny")

from src.config import PRETTY_NAMES, assign_category, BASKET_1_STRATEGY, BASKET_2_STRATEGY

@st.cache_data(ttl=300)
def get_batch_prices(tickers):
    """Pobiera ostatnie ceny dla listy tickerów jednym zapytaniem."""
    if not tickers:
        return {}
    try:
        data = yf.download(tickers, period="2d", progress=False)
        if data.empty:
            return {}
        # Obsługa MultiIndex (nowe yfinance przy wielu tickerach)
        if isinstance(data.columns, pd.MultiIndex):
            close_data = data["Close"]
        else:
            close_data = data[["Close"]]
        # Zwracamy ostatnią dostępną cenę dla każdego tickera
        return close_data.ffill().iloc[-1].to_dict()
    except Exception as e:
        st.toast(f"⚠️ Błąd pobierania cen zbiorczych: {e}", icon="⚠️")
        return {}

db = PortfolioDB()

# --- PANEL BOCZNY (DODAWANIE) ---
st.sidebar.header("Zarządzanie Portfelem")

mode = st.sidebar.radio("Co chcesz dodać?",
                        ["➕ Akcje / ETF / Krypto", "🏦 Obligacje (Skarbowe)", "🥇 Złoto (Gramy)", "🏦 Automat ETF"])

# 1. AKCJE / KRYPTO
if mode == "➕ Akcje / ETF / Krypto":
    with st.sidebar.form("add_stock"):
        st.write("Dodaj aktywo giełdowe")
        ticker = st.text_input("Symbol (np. AAPL, BTC-USD)").upper().strip()
        qty = st.number_input("Ilość sztuk", min_value=0.00000001, format="%.8f")
        price_input = st.number_input("Cena zakupu (za 1 szt.)", min_value=0.01)
        is_pln = st.checkbox("Cena podana w PLN (przelicz)", value=False)

        if st.form_submit_button("Zapisz"):
            final_price = price_input
            if is_pln:
                if "-USD" in ticker or "USD" in ticker:
                    rate = get_exchange_rate("USD", "PLN")
                    final_price = price_input / rate
                elif "-EUR" in ticker or ticker.endswith(".DE"):
                    rate = get_exchange_rate("EUR", "PLN")
                    final_price = price_input / rate
            db.add_position(ticker, qty, final_price)
            st.success("Dodano!")
            st.rerun()

# 2. OBLIGACJE
elif mode == "🏦 Obligacje (Skarbowe)":
    st.sidebar.info("Obligacje o stałym oprocentowaniu.")
    with st.sidebar.form("add_bond"):
        name = st.text_input("Nazwa (np. EDO1034)", "EDO").upper()
        interest = st.number_input("Oprocentowanie (%)", 0.0, 20.0, 6.0, step=0.1)
        amount = st.number_input("Zainwestowana Kwota (PLN)", min_value=100.0, step=100.0)
        maturity_date = st.date_input("Data Wykupu", datetime.now() + timedelta(days=365 * 10))
        bond_ticker = f"#OBLIGACJE_{name}_{interest}%_{maturity_date}"

        if st.form_submit_button("Dodaj Obligacje"):
            db.add_position(bond_ticker, 1.0, amount)
            st.success(f"Dodano {name}!")
            st.rerun()

# 3. ZŁOTO
elif mode == "🥇 Złoto (Gramy)":
    with st.sidebar.form("add_gold"):
        weight_g = st.number_input("Waga (Gramy)", min_value=1.0, step=1.0)
        buy_cost_total = st.number_input("Koszt całkowity (PLN)", min_value=1.0)
        if st.form_submit_button("Dodaj Złoto"):
            oz_qty = weight_g / 31.1034768
            price_per_oz_pln = buy_cost_total / oz_qty
            db.add_position("GC=F", oz_qty, price_per_oz_pln)
            st.success(f"Dodano {weight_g}g złota!")
            st.rerun()

# 4. AUTOMAT ETF (Z WSPARCIEM DLA 2 KOSZYKÓW)
elif mode == "🏦 Automat ETF":
    st.sidebar.markdown("---")
    st.sidebar.info("Symuluje zakup koszyka w wybranym dniu.")

    # Przełącznik wyboru koszyka
    chosen_basket = st.sidebar.radio("Wybierz strategię ETF:", ["Koszyk 1 (Globalny)", "Koszyk 2 (Polska + EM)"])

    with st.sidebar.form("add_basket"):
        total_pln = st.number_input("Kwota do zainwestowania (PLN)", min_value=50.0, step=50.0)
        buy_date = st.date_input("Data zakupu", datetime.now())

        if st.form_submit_button("🚀 Kup Koszyk"):
            progress_bar = st.sidebar.progress(0)
            status_text = st.sidebar.empty()

            # Decydujemy, który słownik pobrać
            active_strategy = BASKET_1_STRATEGY if chosen_basket == "Koszyk 1 (Globalny)" else BASKET_2_STRATEGY

            count = 0
            total_tickers = len(active_strategy)
            is_historical = buy_date < datetime.now().date()

            for ticker, weight in active_strategy.items():
                count += 1
                status_text.write(f"Przetwarzam: {ticker}...")
                progress_bar.progress(count / total_tickers)

                target_pln = total_pln * weight

                try:
                    etf = yf.Ticker(ticker)
                    info = etf.fast_info
                    currency = info.currency
                    if not currency: currency = "USD"
                    if ticker.endswith(".DE"): currency = "EUR"  # Wymuszamy Euro dla giełdy niemieckiej

                    price_native = 0.0

                    if is_historical:
                        price_native = get_historical_price(ticker, buy_date)
                        if price_native is None:
                            st.sidebar.error(f"Brak danych dla {ticker} na {buy_date}")
                            continue
                    else:
                        price_native = info.last_price

                    if not price_native:
                        st.sidebar.error(f"Błąd ceny dla {ticker}")
                        continue

                    fx_rate = get_exchange_rate(currency, "PLN", buy_date if is_historical else None)
                    price_in_pln = price_native * fx_rate
                    qty = target_pln / price_in_pln

                    db.add_position(ticker, qty, price_native)

                except Exception as e:
                    st.sidebar.error(f"Błąd dla {ticker}: {e}")

            progress_bar.empty()
            status_text.write("✅ Gotowe!")
            st.success(f"Zainwestowano {total_pln} PLN w {chosen_basket}.")
            st.rerun()

# --- GŁÓWNA CZĘŚĆ (PRZELICZANIE) ---
df = db.get_portfolio()

if df.empty:
    st.info("Portfel pusty. Dodaj coś po lewej!")
else:
    current_prices = []
    currencies = []
    pln_values = []
    categories = []
    costs_pln_list = []
    something_deleted = False

    # --- BATCH FETCH: pobieramy wszystkie ceny jednym zapytaniem ---
    equity_tickers_list = [t for t in df['ticker'].unique() if not t.startswith("#")]

    batch_prices = get_batch_prices(tuple(equity_tickers_list))

    for i, row in df.iterrows():
        try:
            t = row['ticker']
            qty = row['quantity']
            avg_price = row['avg_price']
            timestamp = row.get('timestamp', None)

            if "#" in t:
                date_match = re.search(r'_(\d{4}-\d{2}-\d{2})$', t)
                if date_match:
                    end_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").date()
                    if datetime.now().date() >= end_date:
                        db.delete_position(row['id'])
                        something_deleted = True
                        continue

            cat = assign_category(t)
            categories.append(cat)

            if t.startswith("#OBLIGACJE"):
                currency = "PLN"
                cost_pln = avg_price * qty
                match = re.search(r'_([\d\.]+)%', t)
                interest_rate = float(match.group(1)) / 100.0 if match else 0.0

                current_val_pln = cost_pln
                if timestamp:
                    buy_date = pd.to_datetime(timestamp)
                    years_held = (datetime.now() - buy_date).days / 365.25
                    if years_held > 0:
                        current_val_pln = cost_pln * ((1 + interest_rate) ** years_held)

                cur_price = current_val_pln / qty
                val_pln = current_val_pln

            else:
                # Waluta określana na podstawie symbolu — bez dodatkowego zapytania do API
                currency = "USD"  # domyślna
                # Próbujemy użyć ceny z batch fetcha, fallback do fast_info
                cur_price = batch_prices.get(t, None)
                if cur_price is None or cur_price == 0:
                    cur_price = float(yf.Ticker(t).fast_info.last_price or avg_price)

                if "-USD" in t:
                    currency = "USD"
                elif t.endswith(".WA"):
                    currency = "PLN"
                elif t.endswith(".DE"):
                    currency = "EUR"
                elif t == "GC=F":
                    currency = "USD"

                fx_rate = get_exchange_rate(currency, "PLN")
                val_pln = qty * cur_price * fx_rate

                if t == "GC=F" and avg_price > 2000:
                    cost_pln = avg_price * qty
                else:
                    cost_pln = avg_price * qty * fx_rate

            current_prices.append(cur_price)
            currencies.append(currency)
            pln_values.append(val_pln)
            costs_pln_list.append(cost_pln)

        except Exception as e:
            failed_ticker = row.get('ticker', '???')
            st.toast(f"⚠️ Nie udało się wycenić: {failed_ticker}", icon="⚠️")
            current_prices.append(0.0)
            currencies.append("ERR")
            pln_values.append(0.0)
            costs_pln_list.append(avg_price * qty)  # Koszt historyczny zamiast 0
            categories.append("Nieznane")

    if something_deleted: st.rerun()

    df['Kategoria'] = categories
    df['Waluta'] = currencies
    df['Obecna Cena'] = current_prices
    df['Wartość (PLN)'] = pln_values
    df['Koszt (PLN)'] = costs_pln_list
    df['Zysk (PLN)'] = df['Wartość (PLN)'] - df['Koszt (PLN)']
    df['Zysk (%)'] = (df['Zysk (PLN)'] / df['Koszt (PLN)']) * 100

    df_grouped = df.groupby('ticker').agg({
        'quantity': 'sum', 'Wartość (PLN)': 'sum', 'Koszt (PLN)': 'sum',
        'Kategoria': 'first', 'Waluta': 'first'
    }).reset_index()

    df_grouped['Zysk (PLN)'] = df_grouped['Wartość (PLN)'] - df_grouped['Koszt (PLN)']
    df_grouped['Zysk (%)'] = (df_grouped['Zysk (PLN)'] / df_grouped['Koszt (PLN)']) * 100
    df_grouped['Nazwa'] = df_grouped['ticker'].map(PRETTY_NAMES).fillna(df_grouped['ticker'])


    def clean_name(name):
        if "#OBLIGACJE" in name:
            parts = name.split('_')
            return f"Obligacje {parts[1]} {parts[2]}"
        return name


    df_grouped['Nazwa'] = df_grouped['Nazwa'].apply(clean_name)

    # --- KPI & KAFELKI ---
    st.markdown("### 📊 Podsumowanie Twojego Majątku")
    k1, k2, k3 = st.columns(3)
    with k1:
        with st.container(border=True):
            st.metric("Wartość Portfela", f"{df_grouped['Wartość (PLN)'].sum():,.2f} PLN")
    with k2:
        with st.container(border=True):
            calkowity_zysk = df_grouped['Zysk (PLN)'].sum()
            st.metric("Całkowity Zysk", f"{calkowity_zysk:+,.2f} PLN", delta_color="normal")
    with k3:
        with st.container(border=True):
            ilosc_pozycji = len(df_grouped)
            st.metric("Ilość Aktywów", f"{ilosc_pozycji}")

    # --- WYKRES HISTORYCZNY (PANCERNA WERSJA) ---
    st.markdown("---")
    st.subheader("📈 Trend Wartości Twojego Obecnego Składu (Ostatnie 6 miesięcy)")

    with st.container(border=True):
        with st.spinner("Przeliczam historyczną wycenę..."):
            try:
                equity_tickers = [t for t in df['ticker'].unique() if not t.startswith("#")]

                if equity_tickers:
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=180)

                    hist_all = yf.download(equity_tickers, start=start_date, progress=False)

                    history_series = []  # ← dodaj tę linię

                    if not hist_all.empty:
                        if isinstance(hist_all.columns, pd.MultiIndex):
                            prices_all = hist_all["Close"]
                        else:
                            prices_all = hist_all[["Close"]]
                            prices_all.columns = equity_tickers

                        for t in equity_tickers:
                            if t not in prices_all.columns:
                                continue
                            qty = df[df['ticker'] == t]['quantity'].sum()
                            curr = "PLN" if t.endswith(".WA") else "EUR" if t.endswith(".DE") else "USD"
                            fx = get_exchange_rate(curr, "PLN")
                            asset_val = prices_all[t] * qty * fx
                            asset_val.name = t
                            history_series.append(asset_val)

                    if history_series:
                        combined_df = pd.concat(history_series, axis=1)
                        combined_df = combined_df.ffill()
                        combined_df = combined_df.bfill()
                        portfolio_history = combined_df.sum(axis=1)

                        if not portfolio_history.empty:
                            import plotly.graph_objects as go

                            fig_hist = go.Figure()
                            fig_hist.add_trace(go.Scatter(
                                x=portfolio_history.index, y=portfolio_history.values,
                                mode='lines', name='Wartość (PLN)',
                                line=dict(color='#D4AF37', width=3)
                            ))
                            fig_hist.update_layout(
                                margin=dict(l=10, r=10, t=10, b=10), height=300,
                                xaxis_title="", yaxis_title="Wartość w PLN", hovermode="x unified",
                                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                            )
                            st.plotly_chart(fig_hist, use_container_width=True, key="portfolio_hist_chart_final")
                        else:
                            st.info("Brak wystarczających, płynnych danych do wyrysowania trendu.")
                    else:
                        st.info("Nie udało się pobrać historii dla Twoich aktywów.")
                else:
                    st.info("Dodaj aktywa giełdowe do portfela, aby zobaczyć historię wyceny.")
            except Exception as e:
                st.error(f"Szczegóły błędu: {e}")

    # --- WYKRESY KOŁOWE ---
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.subheader("📊 Struktura Portfela")
            fig1 = px.pie(df_grouped, values='Wartość (PLN)', names='Nazwa', hole=0.4)
            st.plotly_chart(fig1, use_container_width=True, key="wykres_struktura")
    with c2:
        with st.container(border=True):
            st.subheader("🛡️ Alokacja Ryzyka")
            color_map = {
                "📈 Akcje / ETF": "#636EFA", "🏦 Obligacje / Bezpieczne": "#00CC96",
                "🥇 Surowce / Złoto": "#FFD700", "🪙 Krypto": "#FFA15A"
            }
            fig2 = px.pie(df.groupby('Kategoria')['Wartość (PLN)'].sum().reset_index(),
                          values='Wartość (PLN)', names='Kategoria', hole=0.4, color='Kategoria',
                          color_discrete_map=color_map)
            st.plotly_chart(fig2, use_container_width=True, key="wykres_alokacja")

    # --- DOLNA SEKCJA (RANKING + TABELA) ---
    st.markdown("---")
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("🏆 Liderzy i Maruderzy")
        with st.container(border=True):
            if len(df_grouped) > 1:
                best = df_grouped.sort_values(by='Zysk (%)', ascending=False).iloc[0]
                worst = df_grouped.sort_values(by='Zysk (%)', ascending=True).iloc[0]
                st.markdown("##### 🔥 Najlepszy wynik")
                st.metric(best['Nazwa'], f"{best['Wartość (PLN)']:,.2f} zł", f"{best['Zysk (%)']:+.2f}%")
                st.markdown("---")
                st.markdown("##### 🧊 Najsłabsze ogniwo")
                st.metric(worst['Nazwa'], f"{worst['Wartość (PLN)']:,.2f} zł", f"{worst['Zysk (%)']:+.2f}%")
            else:
                st.info("Dodaj więcej aktywów, aby zobaczyć ranking.")

    with col_right:
        st.subheader("📋 Szczegóły Portfela")
        with st.container(border=True):
            def color_profit(val):
                if isinstance(val, (int, float)):
                    if val > 0:
                        return 'color: #00CC96; font-weight: bold;'
                    elif val < 0:
                        return 'color: #EF553B; font-weight: bold;'
                return 'color: gray;'


            display_df = df_grouped[['Nazwa', 'Kategoria', 'Wartość (PLN)', 'Zysk (PLN)', 'Zysk (%)']].copy()
            try:
                styled_df = display_df.style.map(color_profit, subset=['Zysk (PLN)', 'Zysk (%)'])
            except AttributeError:
                styled_df = display_df.style.applymap(color_profit, subset=['Zysk (PLN)', 'Zysk (%)'])

            styled_df = styled_df.format({
                'Wartość (PLN)': "{:,.2f} zł", 'Zysk (PLN)': "{:+,.2f} zł", 'Zysk (%)': "{:+.2f}%"
            })
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # --- PANEL ZARZĄDZANIA ---
    st.markdown("---")
    with st.expander("🗑️ Zarządzanie (Usuwanie transakcji z bazy)"):
        st.write("Wybierz pozycję, aby trwale ją usunąć.")
        to_del = st.selectbox("Wybierz transakcję (ID : Ticker):", df['id'].astype(str) + " : " + df['ticker'])
        if st.button("Usuń wybraną pozycję"):
            db.delete_position(int(to_del.split(" : ")[0]))
            st.success("Usunięto pomyślnie!")
            st.rerun()

    # --- EXPORT I SYMULATOR CZASU ---
    st.sidebar.markdown("---")
    st.sidebar.header("💾 Bezpieczeństwo")


    def to_excel(df_to_save):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_to_save.to_excel(writer, index=False, sheet_name='Portfel')
        return output.getvalue()


    excel_data = to_excel(df_grouped)
    st.sidebar.download_button(
        label="📥 Pobierz Portfel (.xlsx)", data=excel_data,
        file_name=f'portfel_backup_{datetime.now().strftime("%Y%m%d")}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    st.sidebar.markdown("---")
    st.sidebar.header("🛠️ Symulator Czasu")
    with st.sidebar.expander("Zmiana daty zakupu"):
        options = {f"{row['ticker']} (ID: {row['id']})": row['id'] for index, row in df.iterrows()}
        if options:
            selected_option = st.selectbox("Wybierz pozycję do zmiany:", list(options.keys()))
            new_date = st.date_input("Ustaw datę zakupu na:", datetime.now() - timedelta(days=365))
            if st.button("🕒 Zmień datę i przelicz"):
                try:
                    position_id = options[selected_option]
                    new_timestamp = new_date.strftime("%Y-%m-%d 12:00:00")
                    db.update_timestamp(position_id, new_timestamp)
                    st.toast("Data zmieniona pomyślnie! Odświeżam...", icon="✅")
                    st.rerun()
                except Exception as e:
                    st.error(f"Wystąpił błąd: {e}")
        else:
            st.info("Brak pozycji do edycji.")