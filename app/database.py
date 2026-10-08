from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent.parent / "bookstore.db"

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def initialize_database():
    with get_connection() as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS books ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "title TEXT NOT NULL, author TEXT NOT NULL,"
            "category TEXT NOT NULL CHECK(category IN ('Fiction', 'Non-Fiction')),"
            "format TEXT NOT NULL, language TEXT NOT NULL,"
            "publication_date TEXT NOT NULL,"
            "customer_rating REAL NOT NULL CHECK(customer_rating >= 0 AND customer_rating <= 5),"
            "price REAL NOT NULL CHECK(price >= 0))"
        )
        connection.commit()
