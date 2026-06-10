import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from src.database import PortfolioDB
from src.config import PRETTY_NAMES

st.set_page_config(page_title="Historia Transakcji", layout="wide")
st.title("📜 Historia Transakcji")

db = PortfolioDB()
df = db.get_portfolio()

if df.empty:
    st.info("Brak transakcji w bazie.")
    st.stop()

# --- CZYSZCZENIE DANYCH ---
from src.data import get_exchange_rate

df['timestamp'] = pd.to_datetime(df['timestamp'])
df['Nazwa'] = df['ticker'].map(PRETTY_NAMES).fillna(df['ticker'])

# Przeliczenie wartości zakupu na PLN z uwzględnieniem waluty
def oblicz_wartosc_pln(row):
    t = row['ticker']
    qty = row['quantity']
    price = row['avg_price']
    # Data zakupu do pobrania kursu historycznego
    purchase_date = row['timestamp'].date() if pd.notna(row['timestamp']) else None

    # Obligacje i złoto już są zapisane w PLN
    if t.startswith("#OBLIGACJE"):
        return qty * price
    if t == "GC=F" and price > 2000:
        return qty * price

    # Waluta na podstawie tickera
    if t.endswith(".WA"):
        return qty * price  # PLN, bez przeliczenia
    elif t.endswith(".L"):
        currency = "GBP"
    elif t.endswith(".DE"):
        currency = "EUR"
    else:
        currency = "USD"

    # Kurs z dnia zakupu, nie dzisiejszy
    fx = get_exchange_rate(currency, "PLN", purchase_date)
    return qty * price * fx

df['Wartość zakupu (PLN)'] = df.apply(oblicz_wartosc_pln, axis=1)

# Czytelna nazwa dla obligacji
def clean_name(name):
    if "#OBLIGACJE" in name:
        parts = name.split('_')
        return f"🏦 Obligacje {parts[1]} {parts[2]}"
    return name

df['Nazwa'] = df['Nazwa'].apply(clean_name)

# --- KPI ---
st.markdown("### 📊 Podsumowanie")
k1, k2, k3, k4 = st.columns(4)

with k1:
    with st.container(border=True):
        st.metric("Liczba transakcji", len(df))
with k2:
    with st.container(border=True):
        st.metric("Unikalne aktywa", df['ticker'].nunique())
with k3:
    with st.container(border=True):
        pierwsza = df['timestamp'].min().strftime("%d.%m.%Y")
        st.metric("Pierwsza transakcja", pierwsza)
with k4:
    with st.container(border=True):
        total_wplat = df['Wartość zakupu (PLN)'].sum()
        st.metric("Łączna kwota wpłat", f"{total_wplat:,.0f} PLN")

# --- WYKRES WPŁAT W CZASIE ---
st.markdown("---")
st.subheader("📈 Historia Wpłat w Czasie")

with st.container(border=True):
    df_sorted = df.sort_values('timestamp')
    df_sorted['Skumulowane wpłaty (PLN)'] = df_sorted['Wartość zakupu (PLN)'].cumsum()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_sorted['timestamp'],
        y=df_sorted['Skumulowane wpłaty (PLN)'],
        mode='lines+markers',
        name='Skumulowane wpłaty',
        line=dict(color='#00CC96', width=3),
        marker=dict(size=6),
        hovertemplate='%{x|%d.%m.%Y}<br>Łącznie: %{y:,.0f} PLN<extra></extra>'
    ))
    fig.update_layout(
        height=350,
        hovermode='x unified',
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis_title="PLN",
        xaxis_title=""
    )
    st.plotly_chart(fig, use_container_width=True)

# --- WYKRES WPŁAT PER AKTYWO ---
st.markdown("---")
st.subheader("🏦 Ile Wpłaciłeś w Każde Aktywo")

with st.container(border=True):
    df_per_asset = df.groupby('Nazwa')['Wartość zakupu (PLN)'].sum().sort_values(ascending=True).reset_index()

    fig2 = go.Figure(go.Bar(
        x=df_per_asset['Wartość zakupu (PLN)'],
        y=df_per_asset['Nazwa'],
        orientation='h',
        marker_color='#636EFA',
        text=df_per_asset['Wartość zakupu (PLN)'].apply(lambda x: f"{x:,.0f} PLN"),
        textposition='outside'
    ))
    fig2.update_layout(
        height=400,
        margin=dict(l=20, r=100, t=20, b=20),
        xaxis_title="Wpłacona kwota (PLN)",
        yaxis_title=""
    )
    st.plotly_chart(fig2, use_container_width=True)

# --- TABELA TRANSAKCJI ---
st.markdown("---")
st.subheader("📋 Wszystkie Transakcje")

with st.container(border=True):
    # Filtry
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        dostepne_nazwy = ["Wszystkie"] + sorted(df['Nazwa'].unique().tolist())
        filtr_aktywo = st.selectbox("Filtruj po aktywie:", dostepne_nazwy)
    with col_f2:
        filtr_od = st.date_input("Od daty:", df['timestamp'].min().date())

    df_filtered = df.copy()
    if filtr_aktywo != "Wszystkie":
        df_filtered = df_filtered[df_filtered['Nazwa'] == filtr_aktywo]
    df_filtered = df_filtered[df_filtered['timestamp'].dt.date >= filtr_od]

    display = df_filtered[['timestamp', 'Nazwa', 'quantity', 'avg_price', 'Wartość zakupu (PLN)']].copy()
    display.columns = ['Data', 'Aktywo', 'Ilość', 'Cena zakupu', 'Wartość (PLN)']
    display['Data'] = display['Data'].dt.strftime('%d.%m.%Y %H:%M')
    display = display.sort_values('Data', ascending=False)

    st.dataframe(
        display.style.format({
            'Ilość': '{:.6f}',
            'Cena zakupu': '{:,.4f}',
            'Wartość (PLN)': '{:,.2f} zł'
        }),
        use_container_width=True,
        hide_index=True
    )