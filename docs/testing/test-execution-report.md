# Test Execution Report

## Requirement
Jira EPMCDMETST-68481

## Scope
Non-Fiction and Fiction advanced book filtering (Book Format, Language, Publication Date, Customer Reviews), including the `GET /api/books` filter parameters and the browser UI filter controls.

## Automated Test Coverage
- **API/backend tests** (pytest, FastAPI `TestClient`): run against a temporary seeded SQLite database with the current date frozen at 2026-08-31, so results do not depend on the day the suite runs.
- **Playwright UI tests** (`pytest-playwright`, `tests/ui/test_book_filters_ui.py`): run against the real application served in-process on a free local port, using the same temporary database and frozen date.

## API Test Execution
Command:
```
python -m pytest -v
```

Result:
```
115 passed, 3 warnings, 19 errors
```

All 115 API/backend/unit tests passed. The 19 errors are the 19 Playwright UI tests. They did not run because the local Playwright Chromium browser binary is unavailable (see [Environment Limitation](#environment-limitation)), so the browser could not be launched. These are setup errors caused by the missing browser, not assertion failures in the application or the tests.

## Playwright Test Execution
Command:
```
python -m pytest tests/ui -v --browser-channel msedge
```

Result:
```
19 passed, 3 warnings
```

## Full Test Execution Using Microsoft Edge
Command:
```
python -m pytest -v --browser-channel msedge
```

Result:
```
134 passed, 3 warnings
```

## Input Validation Scenarios (API)
- `format` and `language` are validated against the allowed values (hardcover, paperback, eBook, audiobook; English, Spanish, French, German). Invalid non-empty values (for example `pdf`, `ebook`, `Hardcover`, `Klingon`, `english`, values with surrounding spaces) return HTTP 400, with and without a category. Every valid value is accepted with its exact capitalization.
- `minRating` accepts only 3 and 4. An empty value means no rating filter. `abc`, `3.5`, `0`, `-1` and `5` return HTTP 400 with the same `detail` error shape as the other filters.
- SQL-injection style values in `format` and `language` are rejected with HTTP 400 and the stored data is unchanged.

## UI Scenarios Covered
Expected results are derived from the seed definition and hard-coded date cutoffs, not from the application's filtering code. Result lists are read through `data-testid` and heading-role locators.
1. Fiction and Non-Fiction category controls are available.
2. Non-Fiction shows the four filter groups (Book Format, Language, Publication Date, Customer Reviews) and their options.
3. Language filter (English) shows only matching books.
4. Format + Language combination (hardcover + English) shows only books matching both.
5. Customer Reviews minimum rating: 4 stars and above (Non-Fiction) and 3 stars and above (Fiction).
6. Publication Date last 30 days, last 6 months and last year, each for Non-Fiction (including the inside/outside boundary books) and for Fiction, plus a check that the windows are nested.
7. Clear Filters, for both Fiction and Non-Fiction, resets all four advanced filters, keeps the selected category, and shows the full category list again.
8. Filters persist when switching Fiction to Non-Fiction and Non-Fiction to Fiction, and the same controls and filtering behavior work in both categories.
9. A no-results combination (Fiction + audiobook + German) shows "No books found." and recovers after Clear Filters.

## Environment Limitation
Installation of the Playwright Chromium browser was attempted with:
```
python -m playwright install chromium
```

The download from the Playwright CDN (`cdn.playwright.dev`) timed out, so the Playwright-managed Chromium binary is not installed in this environment. No Playwright test was executed with that binary, and no Chromium-binary test results are claimed in this report.

Microsoft Edge, already installed on the machine, was used successfully through the Playwright browser channel option:
```
--browser-channel msedge
```

Note: pytest labels the UI test IDs `[chromium]` because Edge is a Chromium-based browser driven through Playwright's `chromium` browser type; the tests ran in Microsoft Edge.

Tests were not executed in Firefox or WebKit.

## Warnings
The same three existing deprecation warnings appear in every run that collected the tests:
1. `StarletteDeprecationWarning`: using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead (`fastapi/testclient.py`).
2. `DeprecationWarning`: `on_event` is deprecated, use lifespan event handlers instead (`app/main.py:16`, `@app.on_event("startup")`).
3. `DeprecationWarning`: `on_event` is deprecated, use lifespan event handlers instead (`fastapi/applications.py`, raised by the same startup handler).

No Playwright warnings were reported.

## Conclusion
All 134 automated tests (115 API/backend/unit and 19 Playwright UI) pass when executed using the installed Microsoft Edge browser channel (`--browser-channel msedge`). Running `python -m pytest -v` without the channel option reports 115 passed and 19 errors in this environment, solely because the Playwright Chromium binary could not be downloaded. Running the UI tests in Playwright's bundled Chromium remains pending until it can be installed.
