import pandas as pd
import numpy as np

class StockAnalyzer:
    """
    Klasa analityczna przetwarzająca dane giełdowe na wskaźniki techniczne i metryki ryzyka.
    Wykorzystuje biblioteki Pandas (operacje wektorowe) i NumPy (operacje matematyczne).
    """
    def __init__(self, df):
        self.df = df
        self.rsi = None
        self.volatility = None

    def calculate_returns(self):
        """
        Oblicza dzienne logarytmiczne lub procentowe stopy zwrotu, potrzebne przy dalszych obliczeniach
        """
        self.df['Returns'] = self.df['Close'].pct_change()
        return self.df

    def calculate_volatility(self):
        """
        Oblicza zmienność jako odchylenie standardowe zwrotów.
        """
        if 'Returns' not in self.df.columns:
            self.calculate_returns()
        # std() - Standard Deviation. Mierzy rozrzut wynikow wokol redniej.
        self.volatility = self.df['Returns'].std()
        return self.volatility

    def calculate_ema(self, short_window=12, long_window=26):
        """
        Oblicza Wykładnicze Średnie Kroczące (EMA).
        W przeciwieństwie do zwykłej średniej (SMA), EMA nadaje większą wagę nowszym cenom, dzięki czemu szybciej reaguje na zmiany trendu.
        """
        # ewm (Exponential Weighted Functions) - funkcja Pandas do średnich ważonych
        self.df['EMA_short'] = self.df['Close'].ewm(span=short_window, adjust=False).mean()
        self.df['EMA_long'] = self.df['Close'].ewm(span=long_window, adjust=False).mean()

    def calculate_macd(self):
        """
        Oblicza wskaźnik MACD (Moving Average Convergence Divergence).
        To różnica między szybką a wolną średnią EMA.
        """
        if 'EMA_short' not in self.df.columns:
            self.calculate_ema()
        self.df['MACD'] = self.df['EMA_short'] - self.df['EMA_long']
        self.df['MACD_signal'] = self.df['MACD'].ewm(span=9, adjust=False).mean()

    def calculate_rsi(self, window=14):
        """
        Oblicza RSI (Relative Strength Index).
        Mierzy siłę trendu w skali 0-100 na podstawie średnich wzrostów i spadków.
        """
        #Roznica cen z dnia na dzien
        delta = self.df['Close'].diff()
        #rozdzielenie wzrostow i spadkow
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        #Stosunek srednich wzrostow do srednich spadkow
        rs = gain / loss
        #Formula RSI
        self.df['RSI'] = 100 - (100 / (1 + rs))
        self.rsi = self.df['RSI']
        return self.df['RSI']

    #Metryki Ryzyka
    def get_risk_metrics(self):
        """
        Oblicza wskaźniki efektywności inwestycji: Sharpe Ratio i Max Drawdown.
        """
        if 'Returns' not in self.df.columns:
            self.calculate_returns()

        #Wskaznik Sharpe'a
        mean_return = self.df['Returns'].mean()
        std_return = self.df['Returns'].std()

        if std_return == 0:
            sharpe_ratio = 0
        else:
            # Średni zwrot dzienny / Odchylenie standardowe * Pierwiastek z 252 (dni sesyjne w roku)
            sharpe_ratio = (mean_return / std_return) * np.sqrt(252)

        #Max Drawdown (Maksymalne obsunięcie kapitału)
        #Skumulowany zwrot
        cumulative_returns = (1 + self.df['Returns']).cumprod()
        #Najwyższy szczyt do tej pory (Running Max)
        running_max = cumulative_returns.cummax()
        #Obsunięcie (Drawdown)
        drawdown = (cumulative_returns / running_max) - 1
        #Najgorsze (minimalne) obsunięcie
        max_drawdown = drawdown.min()

        return {
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown
        }

    def basic_stats(self):
        """
        Zwraca podstawowe statystyki opisowe dla szeregu czasowego cen.
        """
        return {
            "średnia cena": self.df['Close'].mean(),
            "mediana ceny": self.df['Close'].median(),
            "min cena": self.df['Close'].min(),
            "max cena": self.df['Close'].max()
        }