from fastapi import APIRouter, HTTPException, Query
from app.database import get_connection
from app.models import Book

router = APIRouter(prefix="/api/books", tags=["books"])

@router.get("", response_model=list[Book])
def list_books(category: str | None = Query(default=None)):
    query = "SELECT * FROM books"
    params = []
    if category:
        if category not in {"Fiction", "Non-Fiction"}:
            raise HTTPException(status_code=400, detail="Unsupported category")
        query += " WHERE category = ?"
        params.append(category)
    query += " ORDER BY id"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [Book(**dict(row)) for row in rows]

@router.get("/{book_id}", response_model=Book)
def get_book(book_id: int):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM books WHERE id = ?", (book_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return Book(**dict(row))
