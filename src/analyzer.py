import pandas as pd
import numpy as np

class StockAnalyzer:
    def __init__(self, df):
        self.df = df
        self.rsi = None
        self.volatility = None

    def calculate_returns(self):
        # Dzienne zwroty procentowe
        self.df['Returns'] = self.df['Close'].pct_change()
        return self.df

    def calculate_volatility(self):
        # Odchylenie standardowe zwrotów (zmienność)
        if 'Returns' not in self.df.columns:
            self.calculate_returns()
        self.volatility = self.df['Returns'].std()
        return self.volatility

    def calculate_ema(self, short_window=12, long_window=26):
        self.df['EMA_short'] = self.df['Close'].ewm(span=short_window, adjust=False).mean()
        self.df['EMA_long'] = self.df['Close'].ewm(span=long_window, adjust=False).mean()

    def calculate_macd(self):
        if 'EMA_short' not in self.df.columns:
            self.calculate_ema()
        self.df['MACD'] = self.df['EMA_short'] - self.df['EMA_long']
        self.df['MACD_signal'] = self.df['MACD'].ewm(span=9, adjust=False).mean()

    def calculate_rsi(self, window=14):
        delta = self.df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        self.df['RSI'] = 100 - (100 / (1 + rs))
        self.rsi = self.df['RSI']
        return self.df['RSI']

    # --- [NOWOŚĆ] Metryki Ryzyka ---
    def get_risk_metrics(self):
        """
        Oblicza Sharpe Ratio i Max Drawdown.
        """
        if 'Returns' not in self.df.columns:
            self.calculate_returns()

        # 1. Sharpe Ratio (uproszczony, zakładając stopę wolną od ryzyka = 0)
        # Średni zwrot dzienny / Odchylenie standardowe * Pierwiastek z 252 (dni sesyjne w roku)
        mean_return = self.df['Returns'].mean()
        std_return = self.df['Returns'].std()

        if std_return == 0:
            sharpe_ratio = 0
        else:
            sharpe_ratio = (mean_return / std_return) * np.sqrt(252)

        # 2. Max Drawdown (Maksymalne obsunięcie kapitału)
        # Obliczamy skumulowany zwrot
        cumulative_returns = (1 + self.df['Returns']).cumprod()
        # Obliczamy najwyższy szczyt do tej pory (Running Max)
        running_max = cumulative_returns.cummax()
        # Obliczamy obsunięcie (Drawdown)
        drawdown = (cumulative_returns / running_max) - 1
        # Wyciągamy najgorsze (minimalne) obsunięcie
        max_drawdown = drawdown.min()

        return {
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown
        }

    def basic_stats(self):
        return {
            "średnia cena": self.df['Close'].mean(),
            "mediana ceny": self.df['Close'].median(),
            "min cena": self.df['Close'].min(),
            "max cena": self.df['Close'].max()
        }