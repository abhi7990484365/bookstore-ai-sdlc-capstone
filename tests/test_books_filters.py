from datetime import date, timedelta
import pytest
from app.filters import publication_cutoff, subtract_months

CATEGORIES = ["Fiction", "Non-Fiction"]
FORMATS = ["hardcover", "paperback", "eBook", "audiobook"]
LANGUAGES = ["English", "Spanish", "French", "German"]
WINDOWS = ["last30days", "last6months", "lastyear"]


def fetch(client, **params):
    response = client.get("/api/books", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def titles(books):
    return {book["title"] for book in books}


def expected(client, predicate, category=None):
    """Independent oracle: filter the unfiltered list in Python."""
    books = fetch(client, category=category) if category else fetch(client)
    return titles([book for book in books if predicate(book)])


def window_start(window):
    return publication_cutoff(window).isoformat()


# Category regression

def test_unfiltered_returns_both_categories(client):
    assert {book["category"] for book in fetch(client)} == set(CATEGORIES)

@pytest.mark.parametrize("category", CATEGORIES)
def test_category_only_returns_that_category(client, category):
    books = fetch(client, category=category)
    assert books
    assert all(book["category"] == category for book in books)

def test_empty_filter_values_are_ignored(client):
    assert fetch(client, category="", format="", language="", publicationDate="", minRating="") == fetch(client)


# Book format

@pytest.mark.parametrize("category", CATEGORIES)
@pytest.mark.parametrize("book_format", FORMATS)
def test_format_filter(client, category, book_format):
    books = fetch(client, category=category, format=book_format)
    assert books
    assert all(b["format"] == book_format and b["category"] == category for b in books)
    assert titles(books) == expected(client, lambda b: b["format"] == book_format, category)


# Language

@pytest.mark.parametrize("category", CATEGORIES)
@pytest.mark.parametrize("language", LANGUAGES)
def test_language_filter(client, category, language):
    books = fetch(client, category=category, language=language)
    assert books
    assert all(b["language"] == language and b["category"] == category for b in books)
    assert titles(books) == expected(client, lambda b: b["language"] == language, category)


# Publication date

@pytest.mark.parametrize("category", CATEGORIES)
@pytest.mark.parametrize("window", WINDOWS)
def test_publication_date_filter(client, category, window):
    start = window_start(window)
    books = fetch(client, category=category, publicationDate=window)
    assert books
    assert all(b["publication_date"] >= start for b in books)
    assert titles(books) == expected(client, lambda b: b["publication_date"] >= start, category)

def test_publication_date_windows_are_nested(client):
    last30 = titles(fetch(client, publicationDate="last30days"))
    last6m = titles(fetch(client, publicationDate="last6months"))
    last_year = titles(fetch(client, publicationDate="lastyear"))
    assert last30 < last6m < last_year

@pytest.mark.parametrize("window,inside,outside", [
    ("last30days", "Thirty Day Mark", "Just Past Thirty Days"),
    ("last6months", "Six Month Mark", "Just Past Six Months"),
    ("lastyear", "One Year Mark", "Just Past One Year"),
])
def test_publication_date_boundaries(client, window, inside, outside):
    found = titles(fetch(client, category="Non-Fiction", publicationDate=window))
    assert inside in found
    assert outside not in found


# Customer reviews

@pytest.mark.parametrize("category", CATEGORIES)
@pytest.mark.parametrize("min_rating", [3, 4])
def test_min_rating_filter(client, category, min_rating):
    books = fetch(client, category=category, minRating=min_rating)
    assert books
    assert all(b["customer_rating"] >= min_rating for b in books)
    assert titles(books) == expected(client, lambda b: b["customer_rating"] >= min_rating, category)

def test_min_rating_boundaries_are_inclusive(client):
    three_plus = titles(fetch(client, minRating=3))
    four_plus = titles(fetch(client, minRating=4))
    assert "Midnight Echoes" in three_plus and "Midnight Echoes" not in four_plus  # 3.0
    assert "Cold Harbor" in four_plus  # 4.0
    assert "Der Letzte Zug" not in three_plus  # 2.9
    assert four_plus < three_plus


# Combined filters (AND)

def test_documented_example_combination(client):
    start = window_start("lastyear")
    books = fetch(client, category="Non-Fiction", format="hardcover",
                  publicationDate="lastyear", minRating=4)
    assert titles(books) == {"History of Modern Cities"}
    assert all(
        b["category"] == "Non-Fiction" and b["format"] == "hardcover"
        and b["publication_date"] >= start and b["customer_rating"] >= 4
        for b in books
    )

@pytest.mark.parametrize("category", CATEGORIES)
def test_all_filters_combine_with_and(client, category):
    start = window_start("lastyear")
    books = fetch(client, category=category, format="paperback", language="English",
                  publicationDate="lastyear", minRating=4)
    assert titles(books) == expected(
        client,
        lambda b: b["format"] == "paperback" and b["language"] == "English"
        and b["publication_date"] >= start and b["customer_rating"] >= 4,
        category,
    )

def test_combined_filters_narrow_single_filter_results(client):
    single = titles(fetch(client, category="Non-Fiction", language="English"))
    combined = titles(fetch(client, category="Non-Fiction", language="English", format="hardcover"))
    assert combined and combined < single

def test_no_match_returns_empty_list(client):
    assert fetch(client, category="Fiction", format="audiobook", language="German") == []


# Clear / reset behaviour (clearing = request with the category only)

@pytest.mark.parametrize("category", CATEGORIES)
def test_clearing_filters_restores_full_category(client, category):
    filtered = fetch(client, category=category, format="hardcover", minRating=4)
    cleared = fetch(client, category=category)
    assert titles(filtered) < titles(cleared)
    assert titles(cleared) == expected(client, lambda b: True, category)


# Consistency between Fiction and Non-Fiction

@pytest.mark.parametrize("filters", [
    {"format": "hardcover"},
    {"language": "Spanish"},
    {"publicationDate": "last6months"},
    {"minRating": 4},
    {"format": "hardcover", "language": "Spanish", "minRating": 4},
])
def test_fiction_and_nonfiction_share_filter_behaviour(client, filters):
    unfiltered = fetch(client)
    for category in CATEGORIES:
        result = titles(fetch(client, category=category, **filters))
        ids_in_category = [b for b in unfiltered if b["category"] == category]
        assert result == titles([b for b in ids_in_category if matches(b, filters)])

def matches(book, filters):
    checks = {
        "format": lambda v: book["format"] == v,
        "language": lambda v: book["language"] == v,
        "publicationDate": lambda v: book["publication_date"] >= window_start(v),
        "minRating": lambda v: book["customer_rating"] >= v,
    }
    return all(checks[key](value) for key, value in filters.items())


# Validation and safety

@pytest.mark.parametrize("params", [
    {"publicationDate": "lastcentury"},
    {"minRating": 2},
    {"category": "Unknown", "format": "hardcover"},
])
def test_invalid_filter_values_return_400(client, params):
    assert client.get("/api/books", params=params).status_code == 400

def assert_rejected(client, **params):
    response = client.get("/api/books", params=params)
    assert response.status_code == 400, response.text
    assert isinstance(response.json()["detail"], str)

@pytest.mark.parametrize("category", [None, *CATEGORIES])
@pytest.mark.parametrize("bad_format", ["pdf", "ebook", "EBOOK", "Hardcover", " hardcover", "hardcover ", "x"])
def test_invalid_format_returns_400(client, category, bad_format):
    params = {"format": bad_format}
    if category:
        params["category"] = category
    assert_rejected(client, **params)

@pytest.mark.parametrize("category", [None, *CATEGORIES])
@pytest.mark.parametrize("bad_language", ["Klingon", "english", "ENGLISH", " English", "English ", "x"])
def test_invalid_language_returns_400(client, category, bad_language):
    params = {"language": bad_language}
    if category:
        params["category"] = category
    assert_rejected(client, **params)

@pytest.mark.parametrize("book_format", FORMATS)
def test_valid_format_values_are_accepted_exactly(client, book_format):
    books = fetch(client, format=book_format)
    assert books
    assert {b["format"] for b in books} == {book_format}

@pytest.mark.parametrize("language", LANGUAGES)
def test_valid_language_values_are_accepted_exactly(client, language):
    books = fetch(client, language=language)
    assert books
    assert {b["language"] for b in books} == {language}

def test_min_rating_empty_means_no_rating_filter(client):
    assert fetch(client, minRating="") == fetch(client)
    assert fetch(client, category="Fiction", minRating="") == fetch(client, category="Fiction")

@pytest.mark.parametrize("bad_rating", ["abc", "3.5", "0", "-1", "5"])
def test_invalid_min_rating_returns_400(client, bad_rating):
    assert_rejected(client, minRating=bad_rating)

@pytest.mark.parametrize("min_rating", [3, 4])
def test_valid_min_rating_is_accepted(client, min_rating):
    books = fetch(client, minRating=min_rating)
    assert books
    assert all(b["customer_rating"] >= min_rating for b in books)

def test_invalid_value_is_rejected_even_alongside_valid_filters(client):
    assert_rejected(client, category="Fiction", format="hardcover", minRating="abc")

def test_sql_injection_attempt_is_rejected_and_leaves_data_intact(client):
    before = fetch(client)
    assert_rejected(client, format="x' OR '1'='1")
    assert_rejected(client, language="x'; DROP TABLE books;--")
    assert fetch(client) == before


# Date helpers

def test_test_clock_is_frozen():
    assert publication_cutoff("last30days").isoformat() == "2026-08-01"
    assert publication_cutoff("last6months").isoformat() == "2026-02-28"
    assert publication_cutoff("lastyear").isoformat() == "2025-08-31"

def test_subtract_months_clamps_to_month_end():
    assert subtract_months(date(2026, 8, 31), 6) == date(2026, 2, 28)
    assert subtract_months(date(2026, 3, 15), 6) == date(2025, 9, 15)

def test_cutoffs_use_calendar_arithmetic():
    today = date(2024, 2, 29)
    assert publication_cutoff("last30days", today) == today - timedelta(days=30)
    assert publication_cutoff("last6months", today) == date(2023, 8, 29)
    assert publication_cutoff("lastyear", today) == date(2023, 2, 28)
