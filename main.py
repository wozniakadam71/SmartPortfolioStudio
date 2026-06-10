from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.database import PortfolioDB

# Inicjalizacja serwera i połączenia z bazą
app = FastAPI(title="Smart Portfolio API")
db = PortfolioDB()


# Model danych - określa, jakich informacji oczekujemy od telefonu
class Transaction(BaseModel):
    ticker: str
    quantity: float
    price: float


# 1. Odczyt portfela (Telefon pyta: "Co mam?")
@app.get("/api/portfolio")
def get_portfolio():
    df = db.get_portfolio()
    if df.empty:
        return {"assets": []}

    # Zamieniamy DataFrame na listę słowników (JSON), którą łatwo wysłać
    assets = df.to_dict(orient="records")
    return {"assets": assets}


# 2. Dodawanie transakcji (Telefon mówi: "Kupiłem to!")
@app.post("/api/portfolio/add")
def add_transaction(item: Transaction):
    try:
        db.add_position(item.ticker.upper(), item.quantity, item.price)
        return {"status": "success", "message": f"Dodano {item.ticker.upper()} do portfela!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 3. Usuwanie transakcji (Telefon mówi: "Usuń pozycję nr 5")
@app.delete("/api/portfolio/delete/{position_id}")
def delete_transaction(position_id: int):
    try:
        db.delete_position(position_id)
        return {"status": "success", "message": "Usunięto pozycję."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))