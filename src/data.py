import streamlit as st
import yfinance as yf
import pandas as pd

class StockData:
    """
    Klasa odpowiedzialna za pobieranie danych giełdowych.
    """
    def __init__(self):
        pass

    #"@" Zapobiega blokowaniu aplikacji przez limity API i przyspiesza działanie, ttl="24h" - że dane są ważne przez dobę.
    @st.cache_data(ttl="24h")
    def get_data(_self, ticker, period="1y", interval="1d"): #"_self" przez charakterystyke Streamlita
        """
        Pobiera historyczne dane dla podanego tickera.
        Używa cache Streamlit, aby nie pobierać tego samego wielokrotnie.
        Cache wygasa po 24 godzinach.
        """
        try:
            #Pobieranie danych z Yahoo Finance
            df = yf.download(ticker, period=period, interval=interval, progress=False)

            #Sprawdzenie czy API dziala
            if df.empty:
                return pd.DataFrame()

            #Naprawa nazw kolumn
            if isinstance(df.columns, pd.MultiIndex): #Czy wymaga naprawy
                #Spłaszczanie nagłówków jeśli są wielopoziomowe
                df.columns = df.columns.get_level_values(0)
            #Usuwanie strefy czasowej z daty (dla wykresów)
            if df.index.tzinfo is not None:
                df.index = df.index.tz_localize(None)
            return df

        except Exception as e:
            #Blad
            st.error(f"Wystąpił błąd podczas pobierania danych dla {ticker}: {e}")
            return pd.DataFrame()

    @st.cache_data(ttl=3600)
    def get_batch_data(_self, ticker_list, start_date=None, period="2y"):
        """
        Pobiera dane dla listy tickerów (optymalizacja zapytań).
        Obsługuje MultiIndex (nowe yfinance).
        """
        try:
            if start_date:
                df = yf.download(ticker_list, start=start_date, progress=False)
            else:
                df = yf.download(ticker_list, period=period, progress=False)
            
            # Obsługa MultiIndex (nowe yfinance)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    # Sprawdzamy poziomy kolumn
                    if 'Close' in df.columns.get_level_values(0):
                        return df.xs('Close', axis=1, level=0)
                    elif 'Close' in df.columns.get_level_values(1):
                         return df.xs('Close', axis=1, level=1)
                else:
                    if 'Close' in df.columns:
                        return df['Close']
            
            # Fallback
            if 'Close' in df: return df['Close']
            return df
        except Exception as e:
            st.error(f"Błąd pobierania danych zbiorczych: {e}")
            return pd.DataFrame()

    def get_ticker_info(self, ticker):
        """
        Pobiera rozszerzone informacje o spółce: sektor, P/E, dywidenda, www.
        Zawiera wszystkie pola potrzebne do Radaru Fundamentalnego.
        """
        try:
            t = yf.Ticker(ticker)
            info = t.info

            return {
                # Podstawowe
                "name": info.get("shortName", ticker),
                "currency": info.get("currency", "USD"),
                "sector": info.get("sector", "Brak danych"),
                "industry": info.get("industry", "Brak danych"),
                "website": info.get("website", None),
                "summary": info.get("longBusinessSummary", None),
                # Wycena
                "market_cap": info.get("marketCap", None),
                "pe_ratio": info.get("trailingPE", None),
                "forward_pe": info.get("forwardPE", None),
                "dividend_yield": info.get("dividendYield", None),
                # Radar fundamentalny
                "trailingPE": info.get("trailingPE", None),
                "totalRevenue": info.get("totalRevenue", None),
                "profitMargins": info.get("profitMargins", None),
                "returnOnEquity": info.get("returnOnEquity", None),
                "debtToEquity": info.get("debtToEquity", None),
                "currentPrice": info.get("currentPrice", None),
                "targetMeanPrice": info.get("targetMeanPrice", None),
            }
        except Exception as e:
            print(f"Błąd pobierania info dla {ticker}: {e}")
            return {"currency": "?", "name": ticker}


# --- FUNKCJE POMOCNICZE (GLOBALNE) ---
from datetime import datetime, timedelta

@st.cache_data(ttl=3600)
def get_exchange_rate(from_currency, to_currency="PLN", date_obj=None):
    """
    Pobiera kurs waluty. Jeśli podano datę, próbuje pobrać kurs historyczny.
    """
    if from_currency == to_currency or not from_currency:
        return 1.0
    
    # Obsługa GBp (pensy) -> GBP
    if from_currency == "GBp":
        from_currency = "GBP"
        # Cena w pensach to 1/100 funta, ale tutaj zwracamy sam kurs waluty
        # Przeliczenie ceny powinno nastąpić przed wywołaniem lub po.
        # W 2_Portfel.py jest logika: price = price / 100
        
    ticker = f"{from_currency}{to_currency}=X"

    try:
        if date_obj and date_obj < datetime.now().date():
            # Kurs historyczny
            end_date = date_obj + timedelta(days=5) # Zakres +5 dni (weekendy)
            hist = yf.Ticker(ticker).history(start=date_obj, end=end_date)
            if not hist.empty:
                return float(hist['Close'].iloc[0])
            return 1.0 # Fallback
        else:
            # Kurs bieżący
            # Używamy fast_info dla szybkości
            data = yf.Ticker(ticker).fast_info
            price = data.last_price
            return float(price) if price else 1.0
    except:
        return 1.0

def get_historical_price(ticker, date_obj):
    """Pobiera cenę zamknięcia z konkretnego dnia (z buforem na weekendy)."""
    try:
        end_date = date_obj + timedelta(days=5)
        hist = yf.Ticker(ticker).history(start=date_obj, end=end_date)
        if not hist.empty:
            return float(hist['Close'].iloc[0])
        return None
    except:
        return None
