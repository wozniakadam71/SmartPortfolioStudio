import pandas as pd

class SimpleBacktester:
    def __init__(self, data: pd.DataFrame, initial_capital: float = 10000.0):
        self.data = data
        self.initial_capital = initial_capital

    def run_strategy(self):
        # 1. Sprawdź czy mamy dane
        if self.data is None or self.data.empty:
            return None

        # 2. Sprawdź czy mamy wystarczająco dużo danych (minimum 2 punkty: start i koniec)
        if len(self.data) < 2:
            print("⚠️ Za mało danych do obliczenia zwrotu (wymagane min. 2 punkty w czasie).")
            return None

        # Cena zakupu (pierwszy dostępny dzień)
        start_price = self.data["Close"].iloc[0]
        # Cena sprzedaży (ostatni dostępny dzień)
        end_price = self.data["Close"].iloc[-1]

        # Zabezpieczenie przed zerową ceną (choć mało prawdopodobne na giełdzie)
        if start_price == 0:
            return None

        shares = self.initial_capital / start_price
        final_value = shares * end_price
        profit = final_value - self.initial_capital
        roi = (profit / self.initial_capital) * 100

        return {
            "start_price": start_price,
            "end_price": end_price,
            "shares": shares,
            "initial_capital": self.initial_capital,
            "final_value": final_value,
            "profit": profit,
            "roi": roi,
            "start_date": self.data.index[0],
            "end_date": self.data.index[-1]
        }