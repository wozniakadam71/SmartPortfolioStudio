import streamlit as st
import yfinance as yf
import pandas as pd

class StockData:
    """
    Klasa odpowiedzialna za pobieranie danych giełdowych.
    """
    def __init__(self):
        pass
    @st.cache_data(ttl="24h")
    def get_data(_self, ticker, period="1y", interval="1d"):
        """
        Pobiera historyczne dane dla podanego tickera.
        Używa cache Streamlit, aby nie pobierać tego samego wielokrotnie.
        Cache wygasa po 24 godzinach.
        """
        try:
            #Pobieranie danych z Yahoo Finance
            df = yf.download(ticker, period=period, interval=interval, progress=False)

            if df.empty:
                return pd.DataFrame()

            #CZYSZCZENIE DANYCH
            #Naprawa nazw kolumn (czasem yfinance zwraca dziwne nagłówki w nowych wersjach)
            if isinstance(df.columns, pd.MultiIndex):
                #Spłaszczanie nagłówków jeśli są wielopoziomowe
                df.columns = df.columns.get_level_values(0)
            #Usuwanie strefy czasowej z daty (dla wykresów)
            if df.index.tzinfo is not None:
                df.index = df.index.tz_localize(None)

            return df

        except Exception as e:
            st.error(f"Wystąpił błąd podczas pobierania danych dla {ticker}: {e}")
            return pd.DataFrame()

    def get_ticker_info(self, ticker):
        """
        Pobiera rozszerzone informacje o spółce: sektor, P/E, dywidenda, www.
        """
        try:
            t = yf.Ticker(ticker)
            info = t.info

            #Pobieranie danych z bezpiecznymi wartościami domyślnymi
            return {
                "name": info.get("shortName", ticker),
                "currency": info.get("currency", "USD"),
                "sector": info.get("sector", "Brak danych"),
                "industry": info.get("industry", "Brak danych"),
                "website": info.get("website", None),
                "market_cap": info.get("marketCap", None),
                "pe_ratio": info.get("trailingPE", None),  # Cena do Zysku (historyczna)
                "forward_pe": info.get("forwardPE", None),  # Cena do Zysku (prognoza)
                "dividend_yield": info.get("dividendYield", None),  # Stopa dywidendy
                "summary": info.get("longBusinessSummary", None)
            }
        except Exception as e:
            #Obsługa błędnego tickera
            print(f"Błąd pobierania info dla {ticker}: {e}")
            return {"currency": "?", "name": ticker}