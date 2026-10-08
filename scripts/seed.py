from app.database import get_connection, initialize_database

BOOKS = [
    ("The Silent Forest","A. Carter","Fiction","hardcover","English","2026-01-12",4.6,24.99),
    ("Moonlit Roads","R. Sharma","Fiction","paperback","English","2025-09-10",4.1,18.50),
    ("The Last Algorithm","M. Stone","Fiction","eBook","Spanish","2025-05-21",3.8,9.99),
    ("History of Modern Cities","L. Green","Non-Fiction","hardcover","English","2026-02-03",4.7,32.00),
    ("Understanding Space","P. Wilson","Non-Fiction","paperback","French","2025-11-18",4.2,21.75),
    ("Everyday Data","N. Patel","Non-Fiction","eBook","German","2025-07-02",3.9,12.49),
]

if __name__ == "__main__":
    initialize_database()
    with get_connection() as connection:
        connection.execute("DELETE FROM books")
        connection.executemany(
            "INSERT INTO books "
            "(title,author,category,format,language,publication_date,customer_rating,price) "
            "VALUES (?,?,?,?,?,?,?,?)",
            BOOKS,
        )
        connection.commit()
    print(f"Seeded {len(BOOKS)} books.")
