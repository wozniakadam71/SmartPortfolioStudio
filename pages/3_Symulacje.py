import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from src.database import PortfolioDB
from src.data import get_exchange_rate

# 1. Konfiguracja strony
st.set_page_config(page_title="Symulator Przyszłości", layout="wide")
st.title("🔮 Kiedy zostanę Rentierem? (Procent Składany)")

# 2. Łączymy się z bazą
db = PortfolioDB()
df = db.get_portfolio()

# --- OBLICZANIE KAPITAŁU STARTOWEGO ---
start_capital = 0.0

if not df.empty:
    with st.spinner('Liczenie wartości Twojego obecnego portfela...'):
        for i, row in df.iterrows():
            try:
                t = row['ticker']
                qty = float(row['quantity'])
                stock = yf.Ticker(t)
                price = stock.fast_info.last_price
                if price is None: continue
                price = float(price)
                curr = stock.fast_info.currency
                if "-USD" in t: curr = "USD"
                if t.endswith(".WA"): curr = "PLN"
                if t.endswith(".L"): curr = "USD"
                if curr == "GBp":
                    price = price / 100.0
                    curr = "GBP"
                fx_rate = get_exchange_rate(curr, "PLN")
                val_pln = qty * price * fx_rate
                start_capital += val_pln
            except Exception:
                pass

# --- PANEL BOCZNY (INPUTY) ---
st.sidebar.header("🎛️ Parametry Symulacji")

initial_balance_input = float(round(start_capital, 2))
initial_balance = st.sidebar.number_input(
    "Kapitał początkowy (PLN)", value=initial_balance_input, step=1000.0, min_value=0.0, format="%.2f"
)
monthly_contribution = st.sidebar.number_input(
    "Miesięczna wpłata (PLN)", value=2000.0, step=100.0, min_value=0.0, format="%.2f"
)
years = st.sidebar.slider("Horyzont czasowy (lata)", min_value=1, max_value=40, value=10)
interest_rate = st.sidebar.slider("Oczekiwany zysk roczny (%)", min_value=1.0, max_value=15.0, value=8.0, step=0.5)

# --- MATEMATYKA ---
months = years * 12
monthly_rate = (interest_rate / 100) / 12

future_values = []
invested_cash = []
dates = []

current_val = float(initial_balance)
total_invested = float(initial_balance)
start_date = pd.Timestamp.now()

for m in range(months + 1):
    future_values.append(current_val)
    invested_cash.append(total_invested)
    dates.append(start_date + pd.DateOffset(months=m))
    current_val = current_val * (1 + monthly_rate)
    current_val += monthly_contribution
    total_invested += monthly_contribution

# --- KPI W KAFELKACH ---
final_value = future_values[-1]
final_invested = invested_cash[-1]
pure_profit = final_value - final_invested
multiplier = final_value / final_invested if final_invested > 0 else 0

st.markdown("### 📊 Wyniki Symulacji")
c1, c2, c3, c4 = st.columns(4)
with c1:
    with st.container(border=True):
        st.metric("🏁 Przewidywany Majątek", f"{final_value:,.0f} PLN")
with c2:
    with st.container(border=True):
        st.metric("💸 Wpłacisz łącznie", f"{final_invested:,.0f} PLN")
with c3:
    with st.container(border=True):
        st.metric("📈 Czysty Zysk", f"{pure_profit:,.0f} PLN", delta="Z rynku")
with c4:
    with st.container(border=True):
        st.metric("Mnożnik Kapitału", f"{multiplier:.2f}x")

# --- WYKRES W KAFELKU ---
st.markdown("---")
with st.container(border=True):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=future_values, mode='lines', name='Majątek z Zyskiem', fill='tozeroy', line=dict(color='#00CC96', width=3)))
    fig.add_trace(go.Scatter(x=dates, y=invested_cash, mode='lines', name='Tylko Wpłaty', line=dict(color='#EF553B', width=2, dash='dash')))

    fig.update_layout(
        title=f"Prognoza: {years} lat, {interest_rate}% zysku rocznie",
        xaxis_title="Rok", yaxis_title="PLN", hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

# --- OPIS W KAFELKU ---
if final_value > 0:
    profit_pct = (pure_profit / final_value) * 100
    cash_pct = (final_invested / final_value) * 100

    with st.container(border=True):
        st.info(f"""
        💡 **Wniosek:**
        Za {years} lat aż **{profit_pct:.1f}%** Twojego majątku to będą darmowe pieniądze wypracowane przez rynek, 
        a tylko **{cash_pct:.1f}%** to Twoje fizyczne wpłaty z kieszeni. To jest właśnie magia procentu składanego!
        """)