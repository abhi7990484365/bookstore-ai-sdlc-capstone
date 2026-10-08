from fastapi import APIRouter, HTTPException, Query
from app.database import get_connection
from app.filters import InvalidFilter, build_books_query
from app.models import Book

router = APIRouter(prefix="/api/books", tags=["books"])

@router.get("", response_model=list[Book])
def list_books(
    category: str | None = Query(default=None),
    book_format: str | None = Query(default=None, alias="format"),
    language: str | None = Query(default=None),
    publication_date: str | None = Query(default=None, alias="publicationDate"),
    min_rating: int | None = Query(default=None, alias="minRating"),
):
    try:
        query, params = build_books_query(
            category, book_format, language, publication_date, min_rating
        )
    except InvalidFilter as error:
        raise HTTPException(status_code=400, detail=str(error))
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
