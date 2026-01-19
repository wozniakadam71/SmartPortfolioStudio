# Smart Portfolio Studio 📈

Aplikacja webowa do analizy fundamentalnej i technicznej rynków finansowych, stworzona w języku Python.

## Autor
**Adam Woźniak**

## Funkcjonalności
1. **Analiza Spółek** - Wykresy, wskaźniki (RSI, MACD, EMA), metryki ryzyka (Sharpe Ratio).
2. **Macierz Korelacji** - Badanie dywersyfikacji portfela i powiązań między aktywami.
3. **Symulator Monte Carlo** - Prognozowanie przyszłych ścieżek cenowych metodą stochastyczną.

## Technologie
* **Python 3.10+**
* **Streamlit** (Interfejs użytkownika)
* **Pandas & NumPy** (Obliczenia finansowe)
* **Plotly** (Interaktywne wizualizacje)
* **Yfinance** (Pobieranie danych giełdowych w czasie rzeczywistym)

## Instrukcja Uruchomienia

Aby uruchomić projekt lokalnie, wykonaj następujące kroki:

### Krok 1: Przygotowanie środowiska
Upewnij się, że masz zainstalowanego Pythona (zalecana wersja 3.10 lub nowsza).
Otwórz terminal (konsolę) w folderze projektu.

*(Opcjonalnie) Zaleca się utworzenie wirtualnego środowiska, aby zachować porządek:*
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```
### Krok 2: Zainstaluj wymagane biblioteki:

```bash
pip install -r requirements.txt
```

### Krok 3: Wpisz w terminal polecenie:

```bash
streamlit run 1_Analiza.py
```
---
*Projekt zrealizowany przy wsparciu sztucznej inteligencji (Google Gemini)