import sqlite3
import pandas as pd
from datetime import datetime


class PortfolioDB:
    def __init__(self, db_name="portfolio.db"):
        # check_same_thread=False jest kluczowe dla Streamlit!
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        # Tworzymy tabelę z kolumną timestamp (Data zakupu)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                quantity REAL NOT NULL,
                avg_price REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def add_position(self, ticker, quantity, price):
        cursor = self.conn.cursor()
        # Przy dodawaniu timestamp wstawi się sam (CURRENT_TIMESTAMP)
        cursor.execute("INSERT INTO portfolio (ticker, quantity, avg_price) VALUES (?, ?, ?)",
                       (ticker, quantity, price))
        self.conn.commit()

    def get_portfolio(self):
        # Pobieramy dane razem z datą zakupu (timestamp)
        query = "SELECT id, ticker, quantity, avg_price, timestamp FROM portfolio"
        try:
            df = pd.read_sql(query, self.conn)
        except Exception:
            # Zabezpieczenie: jeśli masz starą bazę bez kolumny timestamp
            # to pobieramy bez niej, żeby aplikacja się nie wywaliła
            query_old = "SELECT id, ticker, quantity, avg_price FROM portfolio"
            df = pd.read_sql(query_old, self.conn)
        return df

    def delete_position(self, position_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM portfolio WHERE id = ?", (position_id,))
        self.conn.commit()

    def get_tickers(self):
        df = self.get_portfolio()
        if not df.empty:
            return df['ticker'].unique().tolist()
        return []

    # --- TO JEST TA NOWA FUNKCJA, KTÓREJ BRAKOWAŁO ---
    def update_timestamp(self, position_id, new_timestamp):
        """Aktualizuje datę zakupu dla wybranej pozycji."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE portfolio SET timestamp = ? WHERE id = ?", (new_timestamp, position_id))
        self.conn.commit()


class WatchlistDB:
    def __init__(self, db_name="watchlist.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL UNIQUE,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def add_ticker(self, ticker):
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO watchlist (ticker) VALUES (?)", (ticker,))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass  # Already exists

    def remove_ticker(self, ticker):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker,))
        self.conn.commit()

    def get_tickers(self):
        query = "SELECT ticker FROM watchlist"
        try:
            df = pd.read_sql(query, self.conn)
            if not df.empty:
                return df['ticker'].tolist()
        except Exception:
            pass
        return []
