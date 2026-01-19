import pandas as pd

class SimpleBacktester:
    """
    Służy do weryfikacji teoretycznego wyniku inwestycji na danych historycznych.
    W tej wersji implementuje strategię pasywną 'Buy & Hold' (Benchmark).
    """
    def __init__(self, data: pd.DataFrame, initial_capital: float = 10000.0):
        self.data = data
        self.initial_capital = initial_capital

    def run_strategy(self):
        """
        Symuluje zakup aktywów na początku dostępnego okresu i sprzedaż na końcu.
        Zwraca słownik z metrykami wydajności (ROI, Zysk, Wartość końcowa).
        """
        #Sprawdzenie posiadania danych
        if self.data is None or self.data.empty:
            return None

        #Test wystarczająco dużo danych
        if len(self.data) < 2:
            print(" Za mało danych do obliczenia zwrotu (wymagane min. 2 punkty w czasie).")
            return None

        #Cena zakupu (pierwszy dostępny dzień)
        start_price = self.data["Close"].iloc[0]
        #Cena sprzedaży (ostatni dostępny dzień)
        end_price = self.data["Close"].iloc[-1]

        #Zabezpieczenie przed zerową ceną
        if start_price == 0:
            return None

        #Ilosc akcji do kupienia za dostepny kapital
        shares = self.initial_capital / start_price
        #Wycena na koniec okresu
        final_value = shares * end_price
        #Zysk
        profit = final_value - self.initial_capital
        #ROI - stopa zwrotu w procentach
        roi = (profit / self.initial_capital) * 100

        #Zwracanie wyniku jako slownik
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