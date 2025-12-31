import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from src.data import StockData

class PortfolioAnalyzer:
    def __init__(self, tickers, period="6mo", interval="1d"):
        self.tickers = tickers
        self.period = period
        self.interval = interval
        self.data_fetcher = StockData()

    def load_data(self):
        all_data = {}
        for ticker in self.tickers:
            print(f"📊 Pobieram dane dla {ticker}...")
            df = self.data_fetcher.get_data(ticker, period=self.period, interval=self.interval)
            if "Close" in df.columns:
                all_data[ticker] = df["Close"]
        self.data = pd.DataFrame(all_data)
        return self.data

    def calculate_correlations(self):
        returns = self.data.pct_change().dropna()
        corr = returns.corr()
        print("\n📈 Macierz korelacji:")
        print(corr)
        return corr

    def plot_heatmap(self, corr):
        plt.figure(figsize=(8, 6))
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
        plt.title("Korelacje zwrotów dziennych spółek")
        plt.show()

    def export_stats(self, corr, filename="portfolio_stats.csv"):
        corr.to_csv(filename)
        print(f"✅ Zapisano macierz korelacji do pliku: {filename}")

    def plot_comparison(self):
        """
        Rysuje porównanie zwrotów procentowych wszystkich spółek.
        Wartości są znormalizowane do 100 na początku okresu.
        """
        if not hasattr(self, "data"):
            print("❌ Brak danych. Najpierw wywołaj load_data().")
            return

        normalized = self.data / self.data.iloc[0] * 100  # indeks bazowy = 100
        plt.figure(figsize=(10, 6))
        for ticker in normalized.columns:
            plt.plot(normalized.index, normalized[ticker], label=ticker)
        plt.title("📊 Porównanie zwrotów procentowych spółek")
        plt.xlabel("Data")
        plt.ylabel("Wartość względna (100 = początek okresu)")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.show()
