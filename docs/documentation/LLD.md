# Low-Level Design (LLD)

## Advanced Filtering for Non-Fiction Books

| | |
|---|---|
| **Jira story** | EPMCDMETST-68481 |
| **Document date** | 2026-10-08 |
| **Baseline** | `main` at `7ff461d` |
| **Status** | Draft for review |
| **Related documents** | [FRD](FRD.md), [HLD](HLD.md), [TRACEABILITY](TRACEABILITY.md) |

> **Evidence note.** This LLD documents the code as it exists at the baseline commit. File and line references are to that commit. `docs/design/` does not exist, so there was no earlier design to compare against.

---

## 1. Module Map

| File | Lines of interest | Role |
|---|---|---|
| `app/main.py` | 16-18 startup, 20-22 health, 26-36 static files | App creation, table creation on startup, frontend files |
| `app/routes/books.py` | 8-24 `list_books`, 26-34 `get_book` | HTTP layer for the books API |
| `app/filters.py` | 4-8 constants, 11 `InvalidFilter`, 15-20 `subtract_months`, 23-31 `publication_cutoff`, 34-76 `build_books_query` | Validation, date cutoffs, query construction |
| `app/models.py` | 3-12 `Book` | Response model |
| `app/database.py` | 4 `DB_PATH`, 6-9 `get_connection`, 11-23 `initialize_database` | SQLite access and schema |
| `scripts/seed.py` | 6-33 `build_books`, 36-48 `seed_database` | Seed data |
| `frontend/index.html` | 12-16 tabs, 17-52 filter form, 53-55 results | Page structure |
| `frontend/app.js` | 5-6 state, 8-15 `buildUrl`, 17-46 `loadBooks`, 53-75 handlers | Browser behavior |
| `frontend/styles.css` | `.filters`, `.filters label`, `.filters select`, `.clear` | Filter styling |
| `scripts/build.py` | whole file | Deterministic ZIP build |

## 2. API Design

### 2.1 `GET /api/books`

Router: `APIRouter(prefix="/api/books", tags=["books"])`. Response model: `list[Book]`.

All parameters are optional text values (`str | None`).

| Query parameter | Python argument | Allowed values (case-sensitive) | Condition added |
|---|---|---|---|
| `category` | `category` | `Fiction`, `Non-Fiction` | `category = ?` |
| `format` | `book_format` | `hardcover`, `paperback`, `eBook`, `audiobook` | `format = ?` |
| `language` | `language` | `English`, `Spanish`, `French`, `German` | `language = ?` |
| `publicationDate` | `publication_date` | `last30days`, `last6months`, `lastyear` | `publication_date >= ?` (cutoff date) |
| `minRating` | `min_rating` | `3`, `4` | `customer_rating >= ?` (integer 3 or 4) |

`format`, `publicationDate` and `minRating` are declared with `Query(alias=...)`, so the public names differ from the Python argument names.

### 2.2 Responses

**200 OK.** A JSON array of `Book` objects ordered by `id`. An empty array when nothing matches.

```json
[
  {
    "id": 31,
    "title": "History of Modern Cities",
    "author": "L. Green",
    "category": "Non-Fiction",
    "format": "hardcover",
    "language": "English",
    "publication_date": "2026-10-03",
    "customer_rating": 4.7,
    "price": 32.0
  }
]
```

This example is the single result of the documented request on the 2026-10-08 deployment seed (`id` and date depend on the seed run).

Response field names are `snake_case` (`publication_date`, `customer_rating`), while the query parameters are `camelCase` (`publicationDate`, `minRating`).

**400 Bad Request.** `{"detail": "<message>"}`, produced by `HTTPException(status_code=400, detail=str(error))`.

| Rejected parameter | `detail` |
|---|---|
| `category` | `Unsupported category` |
| `format` | `Unsupported format` |
| `language` | `Unsupported language` |
| `publicationDate` | `Unsupported publicationDate` |
| `minRating` | `Unsupported minRating` |

The server reports the **first** invalid value, checked in the order: category, format, language, publicationDate, minRating.

### 2.3 Other endpoints (unchanged by this story)

| Endpoint | Behavior |
|---|---|
| `GET /api/books/{book_id}` | Returns one `Book`, or 404 `{"detail": "Book not found"}`. |
| `GET /api/health` | `{"status": "ok"}` |
| `GET /`, `/app.js`, `/styles.css` | Frontend files (`include_in_schema=False`). |

### 2.4 Request examples

| Request | Result (from the deployment run) |
|---|---|
| `/api/books?category=Non-Fiction` | 200, 12 books |
| `/api/books?category=Non-Fiction&format=hardcover` | 200, 4 books |
| `/api/books?category=Non-Fiction&minRating=4` | 200, 3 books |
| `/api/books?category=Non-Fiction&language=English` | 200, 4 books |
| `/api/books?category=Non-Fiction&publicationDate=last30days` | 200, 3 books |
| `/api/books?category=Non-Fiction&format=hardcover&publicationDate=lastyear&minRating=4` | 200, 1 book: "History of Modern Cities" |
| `/api/books?category=Non-Fiction&format=pdf` | 400 `{"detail":"Unsupported format"}` |

## 3. Filtering Logic

### 3.1 `build_books_query`

Signature: `build_books_query(category, book_format, language, publication_window, min_rating, today=None) -> (query, params)`.

```text
conditions = []; params = []

if category:            validate in CATEGORIES      -> "category = ?"
if book_format:         validate in FORMATS         -> "format = ?"
if language:            validate in LANGUAGES       -> "language = ?"
if publication_window:  cutoff = publication_cutoff(window, today)
                                                    -> "publication_date >= ?"  param = cutoff.isoformat()
if min_rating:          rating = {"3": 3, "4": 4}.get(min_rating)
                        None -> InvalidFilter       -> "customer_rating >= ?"   param = rating

query = "SELECT * FROM books"
if conditions: query += " WHERE " + " AND ".join(conditions)
query += " ORDER BY id"
```

Properties:

- **AND logic:** all conditions are joined with `AND`.
- **Empty means no filter:** each block starts with a truthiness check, so `None` and `""` skip the filter. A non-empty value (including whitespace such as `" English"`) is validated.
- **Validate before use:** an unsupported value raises `InvalidFilter` before any SQL is run.
- **No injection surface:** the query text contains only fixed column names and `?` placeholders. All values travel in `params`.
- **Ordering:** `ORDER BY id`.
- **Testability:** the optional `today` argument lets tests supply the date. The router does not pass it, so production calls use `date.today()`.

Example output for `category=Non-Fiction&format=hardcover&publicationDate=lastyear&minRating=4` run on 2026-10-08:

```text
SELECT * FROM books WHERE category = ? AND format = ? AND publication_date >= ? AND customer_rating >= ? ORDER BY id
params = ["Non-Fiction", "hardcover", "2025-10-08", 4]
```

### 3.2 Publication cutoffs

`publication_cutoff(window, today)`:

| Window | Cutoff |
|---|---|
| `last30days` | `today - 30 days` |
| `last6months` | `subtract_months(today, 6)` |
| `lastyear` | `subtract_months(today, 12)` |
| anything else | raises `InvalidFilter("Unsupported publicationDate")` |

`subtract_months(value, months)` converts the date to a month index (`year * 12 + month - 1 - months`), splits it back into year and month, and sets the day to `min(original day, days in the target month)`.

Worked values with today = **2026-08-31** (these are the values asserted in the Gherkin feature and tests):

| Window | Cutoff | Note |
|---|---|---|
| `last30days` | 2026-08-01 | |
| `last6months` | **2026-02-28** | Month-end clamped: February has 28 days in 2026. |
| `lastyear` | 2025-08-31 | |

The comparison `publication_date >= ?` is a **text comparison** of ISO `YYYY-MM-DD` strings. The cutoff day is included. There is **no upper bound**, so a date later than today also matches (OBS-1).

### 3.3 Router behavior

```text
try:    query, params = build_books_query(category, book_format, language, publication_date, min_rating)
except InvalidFilter as error: raise HTTPException(400, detail=str(error))
with get_connection() as connection: rows = connection.execute(query, params).fetchall()
return [Book(**dict(row)) for row in rows]
```

## 4. Validation Rules

| Input | Rule | Valid examples | Rejected examples (all tested, HTTP 400) |
|---|---|---|---|
| `category` | Exact match to an allowed value | `Fiction`, `Non-Fiction` | `Unknown` |
| `format` | Exact, case-sensitive | `hardcover`, `paperback`, `eBook`, `audiobook` | `pdf`, `ebook`, `EBOOK`, `Hardcover`, `" hardcover"`, `"hardcover "`, `x` |
| `language` | Exact, case-sensitive | `English`, `Spanish`, `French`, `German` | `Klingon`, `english`, `ENGLISH`, `" English"`, `"English "`, `x` |
| `publicationDate` | One of three window names | `last30days`, `last6months`, `lastyear` | `lastcentury` |
| `minRating` | Text equal to `3` or `4` | `3`, `4` | `abc`, `3.5`, `0`, `-1`, `2`, `5` |
| Any | Empty string | `""` | none, treated as no filter |
| Any | SQL-style text | | `x' OR '1'='1` (format), `x'; DROP TABLE books;--` (language). Data unchanged. |

Notes:

- `minRating` is declared as text (`str | None`) in both the router and the builder. Commit `f8b12a7` changed it from `int | None`. Before that change the type was `int`; after it, the application itself checks the value against `"3"` and `"4"`.
- Allow-lists for format and language were added in `f8b12a7`. Before that commit those two values were not validated.
- Repeated parameters (`?format=pdf&format=hardcover`) return 200 and use the last value (OBS-2, not changed).

## 5. Database

### 5.1 `books` table (`app/database.py`, created by `initialize_database` on startup)

| Column | Type | Constraints | Used by |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | ordering, `GET /api/books/{id}` |
| `title` | TEXT | NOT NULL | display |
| `author` | TEXT | NOT NULL | display |
| `category` | TEXT | NOT NULL, `CHECK(category IN ('Fiction','Non-Fiction'))` | **category filter** |
| `format` | TEXT | NOT NULL | **Book Format filter** |
| `language` | TEXT | NOT NULL | **Language filter** |
| `publication_date` | TEXT | NOT NULL (ISO `YYYY-MM-DD`) | **Publication Date filter** |
| `customer_rating` | REAL | NOT NULL, `CHECK(customer_rating >= 0 AND customer_rating <= 5)` | **Customer Reviews filter** |
| `price` | REAL | NOT NULL, `CHECK(price >= 0)` | display |

- **No schema change and no migration** were made for this story. Table creation uses `CREATE TABLE IF NOT EXISTS`.
- `format` and `language` have **no database constraint**. Allowed values are enforced only by `app/filters.py`.
- No indexes are defined. The database file is `bookstore.db` at the repository root and is gitignored.
- `publication_date` is plain text. The filter depends on it being ISO formatted. Missing or malformed dates were not tested.

### 5.2 Response model (`app/models.py`)

`Book`: `id: int`, `title: str`, `author: str`, `category: str`, `format: str`, `language: str`, `publication_date: str`, `customer_rating: float (0 to 5)`, `price: float (>= 0)`.

### 5.3 Seed data (`scripts/seed.py`)

`seed_database(today)` runs `initialize_database()`, `DELETE FROM books`, then inserts 18 rows. Dates are `today - N days` or computed with `publication_cutoff`, so boundaries stay testable on any day.

| Book | Category | Format | Language | Published | Rating |
|---|---|---|---|---|---|
| The Silent Forest | Fiction | hardcover | English | today-10d | 4.6 |
| Moonlit Roads | Fiction | paperback | English | today-100d | 4.1 |
| The Last Algorithm | Fiction | eBook | Spanish | today-200d | 3.8 |
| Midnight Echoes | Fiction | audiobook | French | today-300d | 3.0 |
| Der Letzte Zug | Fiction | paperback | German | today-500d | 2.9 |
| Cold Harbor | Fiction | hardcover | Spanish | today-20d | 4.0 |
| History of Modern Cities | Non-Fiction | hardcover | English | today-5d | 4.7 |
| Understanding Space | Non-Fiction | paperback | French | today-120d | 4.2 |
| Everyday Data | Non-Fiction | eBook | German | today-250d | 3.9 |
| Voices of the Earth | Non-Fiction | audiobook | Spanish | today-20d | 4.0 |
| Economics Explained | Non-Fiction | hardcover | English | today-400d | 3.0 |
| The Quiet Mind | Non-Fiction | audiobook | French | today-700d | 2.9 |
| Thirty Day Mark | Non-Fiction | paperback | English | **= 30-day cutoff** | 3.5 |
| Just Past Thirty Days | Non-Fiction | paperback | English | cutoff - 1 day | 3.5 |
| Six Month Mark | Non-Fiction | eBook | German | **= 6-month cutoff** | 3.5 |
| Just Past Six Months | Non-Fiction | eBook | German | cutoff - 1 day | 3.5 |
| One Year Mark | Non-Fiction | hardcover | Spanish | **= 1-year cutoff** | 3.5 |
| Just Past One Year | Non-Fiction | hardcover | Spanish | cutoff - 1 day | 3.5 |

6 Fiction and 12 Non-Fiction books. Prices are also seeded (not shown). Ratings of 3.0, 2.9 and 4.0 sit on the rating boundaries.

`AUTOINCREMENT` ids keep counting after `DELETE`, which is consistent with the deployment report showing ids 31 to 42 (inference). Ids are therefore not stable across reseeds. The repository tests do not assert on specific ids, apart from `/api/books/999999` in the 404 test.

## 6. Frontend Design

### 6.1 Page structure (`frontend/index.html`)

| Element | Identifier | Behavior |
|---|---|---|
| Category buttons | `.tab`, `data-category` = `""`, `Fiction`, `Non-Fiction` | Labels: All Books (active initially), Fiction Books, Non-Fiction Books |
| Book Format select | `#filter-format` | Any (`""`), hardcover, paperback, eBook, audiobook (labels capitalized except eBook) |
| Language select | `#filter-language` | Any, English, Spanish, French, German |
| Publication Date select | `#filter-publicationDate` | Any time, Last 30 days, Last 6 months, Last year |
| Customer Reviews select | `#filter-minRating` | Any rating, 3 stars and above (`3`), 4 stars and above (`4`) |
| Clear button | `#clear-filters` | `type="button"` |
| Heading | `#section-title` | "All Books", "Fiction Books" or "Non-Fiction Books" |
| Result container | `#book-list` (`aria-live="polite"`) | Cards, or a message paragraph |
| Error paragraph | `#error` (`hidden` by default) | Failure message |

The select element ids are derived as `filter-` + the state key, which `app.js` relies on.

### 6.2 State (`frontend/app.js`)

```js
const FILTER_KEYS = ["format", "language", "publicationDate", "minRating"];
const state = { category: "", format: "", language: "", publicationDate: "", minRating: "" };
```

- State is in memory only. A reload returns every value to `""`.
- The state keys equal the API query parameter names.

### 6.3 Behavior

| Trigger | Handler action |
|---|---|
| Page load | `loadBooks()` runs with the empty state (All Books, no filters). |
| Click a category tab | Move the `active` class to the clicked tab, set `state.category`, call `loadBooks()`. **The four filters are not touched.** (FR-10) |
| Change a filter select | Set `state[key]` to the selected value, call `loadBooks()`. |
| Click Clear Filters | Set the four filter keys to `""`, set each select's `value` to `""`, call `loadBooks()`. **`state.category` and the active tab are not changed.** (FR-09) |

`buildUrl()` adds only non-empty values, in the order `category`, `format`, `language`, `publicationDate`, `minRating`, using `URLSearchParams`. With nothing set the URL is `/api/books`.

`loadBooks()` flow:

1. Hide the error paragraph. Show "Loading..." in the list.
2. `fetch(buildUrl())`. If the response is not OK, throw `Error("HTTP <status>")`.
3. Parse the JSON array and set the heading to `<category> Books`, or "All Books" when no category is set.
4. If the array is empty, show **"No books found."** and stop.
5. Otherwise render one `<article class="book-card" data-testid="book-card">` per book showing title, author, category, format, language, published date, rating and price (`$` + two decimals). Text values pass through `escapeHtml`.
6. On any failure: empty the list, set the error text **"Unable to load books. Please try again."**, show it, and log the error to the console.

### 6.4 UI states

| State | Condition | What the customer sees |
|---|---|---|
| Loading | Request in flight | "Loading..." |
| Results | 200 with one or more books | Book cards |
| Empty | 200 with an empty array | "No books found." (heading still shows the category) |
| Error | Network failure or non-OK response | Empty list and the error message |

### 6.5 Frontend behaviors to be aware of (from the code)

- The heading is updated only after a **successful** response. After a failed request the heading keeps its previous text while the active tab has already changed.
- The browser never reads the API's `detail` text. Any non-OK response shows the same generic message. The UI offers only valid options, so a 400 is not expected from normal use.
- Requests are not cancelled. If responses arrive out of order, an older response can overwrite a newer one (OBS-3, not reproduced).
- The selects are the only source of filter values, so the UI cannot send an unsupported value without manual tampering.

## 7. Error Handling Summary

| Layer | Error | Handling |
|---|---|---|
| `filters.py` | Unsupported non-empty value | Raises `InvalidFilter(message)` |
| `routes/books.py` | `InvalidFilter` | HTTP 400, `detail` = message |
| `routes/books.py` | Unknown book id | HTTP 404 `Book not found` |
| `frontend/app.js` | Network error, non-OK status | Generic error message, empty list, console log |

## 8. Test Design

| Suite | File | Tests | Approach |
|---|---|---|---|
| API/regression | `tests/test_books_api.py` | 5 | Health, listing, Non-Fiction category, invalid category (400), missing book (404) |
| API/unit | `tests/test_books_filters.py` | 110 | Parameterized by category, format, language, window and rating. Compares against the unfiltered list filtered in Python. Covers boundaries, nesting, AND, parity, validation and date helpers. |
| UI | `tests/ui/test_book_filters_ui.py` | 19 | Playwright. Expectations come from the seed definition and hard-coded cutoffs. Lists are read through `data-testid` and heading-role locators. |

Fixtures:

- `tests/conftest.py` (session, autouse): points `app.database.DB_PATH` at a temporary file, replaces `date` in `app.filters` with a class whose `today()` returns **2026-08-31**, and seeds the database with that date.
- `tests/ui/conftest.py`: starts the real app with Uvicorn on a free port in a background thread and uses it as `base_url`.

Execution results are recorded in `docs/testing/test-execution-report.md` and `docs/testing/test-validation-report.md`: **134 passed, 0 failed** in Microsoft Edge (`python -m pytest -v --browser-channel msedge`). Without the channel option the 19 UI tests error at browser launch on the development machine because Playwright's Chromium is not installed.

## 9. Build Script Design (`scripts/build.py`)

| Element | Detail |
|---|---|
| Command | `python scripts/build.py` (standard library only) |
| Output | `dist/bookstore-ai-sdlc-capstone.zip` |
| Included | `app`, `frontend`, `scripts`, `tests`, `docs`, plus `requirements.txt`, `README.md`, `.gitignore`, `PROJECT_STATUS.md` |
| Excluded directories | `.git`, `.venv`, `venv`, `__pycache__`, `.idea`, `.claude`, `.codemie`, `dist`, `.pytest_cache` |
| Excluded patterns | `*.pyc`, `*.pyo`, `*.db`, `*.sqlite`, `.env` |
| Required files | `app/main.py`, `frontend/index.html`, `scripts/seed.py`, `scripts/build.py`, `requirements.txt`, `README.md`, `.gitignore` (build fails if any is missing) |
| Determinism | Entries sorted by name. Timestamp fixed at 1980-01-01. File mode `0o644`. Fixed compression (deflate, level 9). |
| Safety | Writes to a `.zip.part` file, verifies it (`testzip()` and entry list equals the expected list), then renames it to the final name. |
| Output text | Artifact path, size, SHA-256, file list, then `BUILD SUCCESS` (exit 0), or `BUILD FAILURE: <reason>` on stderr (exit 1). |

## 10. Known Limitations (design level)

| # | Limitation | Reference |
|---|---|---|
| 1 | Publication filter has no upper bound. | OBS-1 |
| 2 | Repeated query parameters are accepted. | OBS-2 |
| 3 | No request cancellation in the browser. | OBS-3 |
| 4 | Allowed values are defined in two places (`filters.py` and `index.html`). | code |
| 5 | `format` and `language` have no database constraint. | `app/database.py` |
| 6 | No index, no pagination. Performance with large data was not tested. | code; validation report |
| 7 | The load-failure message has no automated test. | validation report |
