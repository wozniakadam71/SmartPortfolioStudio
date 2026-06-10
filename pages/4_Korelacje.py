import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from src.database import PortfolioDB

st.set_page_config(page_title="Korelacje", layout="wide")
st.title("🔗 Mapa Korelacji Aktywów")

db = PortfolioDB()
df_portfolio = db.get_portfolio()

if df_portfolio.empty:
    st.info("Portfel jest pusty.")
else:
    df_portfolio['ticker'] = df_portfolio['ticker'].astype(str)
    tickers = [t for t in df_portfolio['ticker'].unique() if not t.startswith("#")]

    if len(tickers) < 2:
        st.warning("⚠️ Potrzebujesz co najmniej 2 aktywów giełdowych do zbadania korelacji.")
    else:
        # Czysty kafelek z informacją
        with st.container(border=True):
            col_info, col_legend = st.columns([1, 2])
            with col_info:
                st.write("**Analizowane aktywa:**")
                for t in tickers:
                    st.write(f"▪️ {t}")
            with col_legend:
                st.markdown("""
                **Jak czytać mapę?**
                * 🟥 **Blisko 1.0:** Aktywa chodzą identycznie (ryzyko braku dywersyfikacji).
                * ⬜ **Ok. 0.0:** Pełna niezależność.
                * 🟦 **Blisko -1.0:** Odwrotność (świetny hedging).
                """)


        @st.cache_data(ttl=3600)
        def get_prices(ticker_list):
            start_date = datetime.now() - timedelta(days=365)
            data = yf.download(ticker_list, start=start_date, progress=False)
            if 'Adj Close' in data:
                return data['Adj Close']
            elif 'Close' in data:
                return data['Close']
            else:
                return data.iloc[:, :len(ticker_list)]


        with st.spinner('Pobieram dane i rysuję wykres...'):
            try:
                df_prices = get_prices(tickers)
                if isinstance(df_prices, pd.Series): df_prices = df_prices.to_frame()
                df_prices = df_prices.dropna(axis=1, how='all').dropna()

                if df_prices.shape[1] < 2:
                    st.error("Brak wystarczających danych.")
                else:
                    returns = df_prices.pct_change().dropna()
                    corr_matrix = returns.corr()

                    # Duży kafelek z wykresem
                    with st.container(border=True):
                        fig = px.imshow(
                            corr_matrix,
                            text_auto=".2f",
                            aspect="auto",
                            color_continuous_scale='RdBu_r',
                            zmin=-1, zmax=1,
                            labels=dict(color="Korelacja")
                        )
                        fig.update_layout(height=600, margin=dict(t=30, b=30, l=30, r=30))
                        st.plotly_chart(fig, use_container_width=True, key="korelacje_heatmap")

            except Exception as e:
                st.error(f"Wystąpił błąd: {e}")