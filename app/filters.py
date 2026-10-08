import calendar
from datetime import date, timedelta

CATEGORIES = ("Fiction", "Non-Fiction")
PUBLICATION_WINDOWS = ("last30days", "last6months", "lastyear")
MIN_RATINGS = (3, 4)


class InvalidFilter(ValueError):
    pass


def subtract_months(value: date, months: int) -> date:
    index = value.year * 12 + (value.month - 1) - months
    year, month = divmod(index, 12)
    month += 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def publication_cutoff(window: str, today: date | None = None) -> date:
    today = today or date.today()
    if window == "last30days":
        return today - timedelta(days=30)
    if window == "last6months":
        return subtract_months(today, 6)
    if window == "lastyear":
        return subtract_months(today, 12)
    raise InvalidFilter("Unsupported publicationDate")


def build_books_query(
    category: str | None = None,
    book_format: str | None = None,
    language: str | None = None,
    publication_window: str | None = None,
    min_rating: int | None = None,
    today: date | None = None,
) -> tuple[str, list]:
    """Build one parameterized query shared by every category; filters combine with AND."""
    conditions: list[str] = []
    params: list = []

    if category:
        if category not in CATEGORIES:
            raise InvalidFilter("Unsupported category")
        conditions.append("category = ?")
        params.append(category)
    if book_format:
        conditions.append("format = ?")
        params.append(book_format)
    if language:
        conditions.append("language = ?")
        params.append(language)
    if publication_window:
        cutoff = publication_cutoff(publication_window, today)
        conditions.append("publication_date >= ?")
        params.append(cutoff.isoformat())
    if min_rating is not None:
        if min_rating not in MIN_RATINGS:
            raise InvalidFilter("Unsupported minRating")
        conditions.append("customer_rating >= ?")
        params.append(min_rating)

    query = "SELECT * FROM books"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id"
    return query, params
