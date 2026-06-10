import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from datetime import datetime, timedelta
from src.database import PortfolioDB

try:
    from pypfopt import EfficientFrontier, risk_models, expected_returns
except ImportError:
    st.error("Biblioteka 'PyPortfolioOpt' nie jest zainstalowana.")
    st.stop()

st.set_page_config(page_title="Optymalizator", layout="wide")
st.title("🧠 Optymalizator Portfela")

db = PortfolioDB()
df_portfolio = db.get_portfolio()

if df_portfolio.empty:
    st.warning("Portfel jest pusty.")
else:
    df_portfolio['ticker'] = df_portfolio['ticker'].astype(str)
    tickers = [t for t in df_portfolio['ticker'].unique() if not t.startswith("#")]

    if len(tickers) < 2:
        st.info("Dodaj co najmniej 2 aktywa giełdowe, aby użyć algorytmu Markowitza.")
    else:
        with st.container(border=True):
            st.write(f"**Analizowane aktywa:** {', '.join(tickers)}")


        @st.cache_data(ttl=3600)
        def get_historical_data(ticker_list):
            start_date = datetime.now() - timedelta(days=365 * 2)
            data = yf.download(ticker_list, start=start_date, progress=False)['Close']
            return data


        with st.spinner("Przeliczanie wariancji i kowariancji..."):
            try:
                df_prices = get_historical_data(tickers)
                df_prices = df_prices.dropna(axis=1, how='all').dropna()

                if df_prices.empty or df_prices.shape[1] < 2:
                    st.error("Za mało danych historycznych do analizy.")
                else:
                    mu = expected_returns.mean_historical_return(df_prices)
                    S = risk_models.sample_cov(df_prices)
                    ef = EfficientFrontier(mu, S)
                    weights = ef.max_sharpe()
                    cleaned_weights = ef.clean_weights()
                    perf = ef.portfolio_performance(verbose=False)

                    st.markdown("### 🏆 Idealny Portfel (Maksymalny Zysk / Ryzyko)")

                    # Trzy kafelki z metrykami
                    k1, k2, k3 = st.columns(3)
                    with k1:
                        with st.container(border=True):
                            st.metric("Przewidywany Zwrot", f"{perf[0] * 100:.2f}%", "Rocznie")
                    with k2:
                        with st.container(border=True):
                            st.metric("Ryzyko (Zmienność)", f"{perf[1] * 100:.2f}%", delta_color="inverse")
                    with k3:
                        with st.container(border=True):
                            st.metric("Wskaźnik Sharpe'a", f"{perf[2]:.2f}", "Jakość portfela")

                    st.markdown("---")

                    c1, c2 = st.columns(2)

                    with c1:
                        with st.container(border=True):
                            st.subheader("⚖️ Sugerowane Wagi")
                            df_weights = pd.DataFrame.from_dict(cleaned_weights, orient='index', columns=['Waga'])
                            df_weights = df_weights[df_weights['Waga'] > 0.0001]
                            fig1 = px.pie(df_weights, values='Waga', names=df_weights.index, hole=0.4)
                            fig1.update_layout(margin=dict(t=20, b=20, l=20, r=20))
                            st.plotly_chart(fig1, use_container_width=True, key="opt_pie")

                    with c2:
                        with st.container(border=True):
                            st.subheader("🆚 Twój Portfel vs Matematyka")
                            current_prices_latest = df_prices.iloc[-1]
                            my_total_value = 0.0
                            my_weights = {}

                            for t in tickers:
                                if t in current_prices_latest:
                                    qty = df_portfolio[df_portfolio['ticker'] == t]['quantity'].sum()
                                    val = qty * current_prices_latest[t]
                                    my_weights[t] = val
                                    my_total_value += val

                            if my_total_value > 0:
                                comparison_data = []
                                for t in tickers:
                                    if t in my_weights:
                                        comparison_data.append({
                                            "Ticker": t,
                                            "Obecnie (%)": (my_weights[t] / my_total_value) * 100,
                                            "Docelowo (%)": cleaned_weights.get(t, 0) * 100
                                        })
                                df_comp = pd.DataFrame(comparison_data).set_index("Ticker")

                                # Wykres słupkowy zgrupowany
                                fig2 = px.bar(df_comp, barmode='group', labels={'value': 'Waga %'})
                                fig2.update_layout(margin=dict(t=20, b=20, l=20, r=20), legend_title_text=None)
                                st.plotly_chart(fig2, use_container_width=True, key="opt_bar")
                            else:
                                st.info("Dodaj wartościowe pozycje do portfela, by zobaczyć porównanie.")

            except Exception as e:
                st.error(f"Wystąpił błąd obliczeń: {e}")