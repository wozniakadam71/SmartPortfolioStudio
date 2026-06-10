# Konfiguracja i stałe dla całej aplikacji

# Ładne nazwy dla tickerów
# config.py — uzupełnij PRETTY_NAMES o brakujące wpisy
PRETTY_NAMES = {
    # ETF Globalny
    "CSPX.L": "🇺🇸 S&P 500",
    "IWDA.L": "🌍 Rynki Rozwinięte",
    "VWRA.L": "🌎 Cały Świat",
    "CNDX.L": "💻 NASDAQ 100",
    # ETF Polska + EM
    "IBCJ.DE": "🇵🇱 MSCI Poland (ETF)",
    "IS3N.DE": "🌏 Wschodzące EM (ETF)",
    # Polskie akcje
    "XTB.WA": "🇵🇱 XTB",
    "TOA.WA": "🇵🇱 Tower Asset",
    "LPP.WA": "🇵🇱 LPP",
    "DNP.WA": "🇵🇱 Dino Polska",
    "APM": "🇺🇸 Aptorum Group",
    # Surowce
    "GC=F": "🥇 Złoto (Spot)",
    "GLD": "🥇 Złoto (ETF)",
    # Krypto
    "BTC-USD": "₿ Bitcoin",
    "ETH-USD": "Ξ Ethereum",
    "XRP-USD": "✕ XRP",
    # Indeksy
    "ES=F": "🇺🇸 S&P 500 (Fut)",
    "^GDAXI": "🇩🇪 DAX"
}

# Główne indeksy rynkowe (używane w 0_Start.py)
MARKET_INDICES = {
    "🇺🇸 S&P 500": "ES=F",
    "🇩🇪 DAX": "^GDAXI",
    "₿ Bitcoin": "BTC-USD",
    "🥇 Złoto": "GC=F"
}

# --- KATEGORIE ---
def assign_category(ticker):
    """Zwraca kategorię aktywa na podstawie symbolu."""
    t = ticker.upper()
    if "OBLIGACJE" in t or t.startswith("#"): return "🏦 Obligacje / Bezpieczne"
    if "GC=F" in t or "GLD" in t or "GOLD" in t or "SI=F" in t: return "🥇 Surowce / Złoto"
    if "BTC" in t or "ETH" in t or "-USD" in t or "-EUR" in t or "CRYPTO" in t: return "🪙 Krypto"
    return "📈 Akcje / ETF"

BASKET_1_STRATEGY = {
    "CSPX.L": 0.25,
    "IWDA.L": 0.25,
    "VWRA.L": 0.25,
    "CNDX.L": 0.25
}

BASKET_2_STRATEGY = {
    "IBCJ.DE": 0.30,
    "IS3N.DE": 0.70
}