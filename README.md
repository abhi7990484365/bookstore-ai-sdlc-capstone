# Bookstore AI SDLC Capstone

Step 1 application foundation for the CodeMie AI-Assistant-Driven SDLC capstone.

## Stack
- Python 3.11+
- FastAPI
- SQLite
- HTML/CSS/JavaScript
- pytest

## Run
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.seed
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000
API docs: http://127.0.0.1:8000/docs

## Filtering
`GET /api/books` accepts optional, AND-combined filters that work the same for Fiction and Non-Fiction:
`category`, `format` (hardcover, paperback, eBook, audiobook), `language` (English, Spanish, French, German),
`publicationDate` (last30days, last6months, lastyear) and `minRating` (3 or 4).

Values are case-sensitive (for example `eBook`, not `ebook`). An empty value (e.g. `minRating=`) means
"no filter". Any other unsupported value for `category`, `format`, `language`, `publicationDate` or
`minRating` (such as `format=pdf`, `minRating=abc`, `3.5`, `0`, `-1` or `5`) returns HTTP 400 with a
`detail` message.

Example: `/api/books?category=Non-Fiction&format=hardcover&publicationDate=lastyear&minRating=4`

Seed dates are relative to the day you run the seed, so re-run `python -m scripts.seed` to refresh them.

### Design notes (EPMCDMETST-68481)
- **Rating column:** the existing `books` table stores customer review ratings in `customer_rating`
  (REAL, 0-5). The column was deliberately not renamed to `customer_reviews`.
- **`minRating` mapping:** `minRating=N` maps to `customer_rating >= N` (supported values: 3 and 4).
- **No migration:** `format`, `language`, `publication_date` and `customer_rating` already existed,
  so no schema change or migration was required. Only the seed data was extended.
- **Filters persist across categories (intentional):** in the UI, switching between All Books,
  Fiction Books and Non-Fiction Books keeps the selected advanced filters, so the same filter
  set can be compared across categories. Only **Clear Filters** resets them, and it keeps the
  selected category.

## Tests
```bash
python -m pytest
```
UI tests (`tests/ui`) use Playwright via `pytest-playwright`. One-time browser setup:
```bash
python -m playwright install chromium
```
If the Chromium download is blocked, run against an installed browser instead, e.g.
`python -m pytest --browser-channel msedge` (or `chrome`).
The UI tests start the app in-process on a free port, so no server needs to be running.

The tests run against a temporary seeded database with "today" frozen at 2026-08-31, so
date-window results do not depend on the day the suite runs.
