from datetime import date, timedelta
from app.database import get_connection, initialize_database
from app.filters import publication_cutoff


def build_books(today: date | None = None):
    """Seed rows with dates relative to today so filter boundaries stay testable."""
    today = today or date.today()
    ago = lambda days: (today - timedelta(days=days)).isoformat()
    day = timedelta(days=1)
    d30 = publication_cutoff("last30days", today)
    d6m = publication_cutoff("last6months", today)
    d1y = publication_cutoff("lastyear", today)
    return [
        ("The Silent Forest","A. Carter","Fiction","hardcover","English",ago(10),4.6,24.99),
        ("Moonlit Roads","R. Sharma","Fiction","paperback","English",ago(100),4.1,18.50),
        ("The Last Algorithm","M. Stone","Fiction","eBook","Spanish",ago(200),3.8,9.99),
        ("Midnight Echoes","C. Dubois","Fiction","audiobook","French",ago(300),3.0,14.99),
        ("Der Letzte Zug","K. Weber","Fiction","paperback","German",ago(500),2.9,11.25),
        ("Cold Harbor","J. Moreno","Fiction","hardcover","Spanish",ago(20),4.0,27.00),
        ("History of Modern Cities","L. Green","Non-Fiction","hardcover","English",ago(5),4.7,32.00),
        ("Understanding Space","P. Wilson","Non-Fiction","paperback","French",ago(120),4.2,21.75),
        ("Everyday Data","N. Patel","Non-Fiction","eBook","German",ago(250),3.9,12.49),
        ("Voices of the Earth","S. Alvarez","Non-Fiction","audiobook","Spanish",ago(20),4.0,16.80),
        ("Economics Explained","T. Brooks","Non-Fiction","hardcover","English",ago(400),3.0,29.50),
        ("The Quiet Mind","H. Laurent","Non-Fiction","audiobook","French",ago(700),2.9,13.40),
        ("Thirty Day Mark","B. Cole","Non-Fiction","paperback","English",d30.isoformat(),3.5,15.00),
        ("Just Past Thirty Days","B. Cole","Non-Fiction","paperback","English",(d30 - day).isoformat(),3.5,15.00),
        ("Six Month Mark","D. Ford","Non-Fiction","eBook","German",d6m.isoformat(),3.5,8.00),
        ("Just Past Six Months","D. Ford","Non-Fiction","eBook","German",(d6m - day).isoformat(),3.5,8.00),
        ("One Year Mark","E. Grant","Non-Fiction","hardcover","Spanish",d1y.isoformat(),3.5,26.00),
        ("Just Past One Year","E. Grant","Non-Fiction","hardcover","Spanish",(d1y - day).isoformat(),3.5,26.00),
    ]


def seed_database(today: date | None = None) -> int:
    books = build_books(today)
    initialize_database()
    with get_connection() as connection:
        connection.execute("DELETE FROM books")
        connection.executemany(
            "INSERT INTO books "
            "(title,author,category,format,language,publication_date,customer_rating,price) "
            "VALUES (?,?,?,?,?,?,?,?)",
            books,
        )
        connection.commit()
    return len(books)


if __name__ == "__main__":
    print(f"Seeded {seed_database()} books.")
