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
60 passed, 3 warnings, 8 errors
```

All 60 API/backend tests passed. The 8 errors are the 8 Playwright UI tests. They did not run because the local Playwright Chromium browser binary is unavailable (see [Environment Limitation](#environment-limitation)), so the browser could not be launched. These are setup errors caused by the missing browser, not assertion failures in the application or the tests.

## Playwright Test Execution
Command:
```
python -m pytest tests/ui -v --browser-channel msedge
```

Result:
```
8 passed, 3 warnings
```

## Full Test Execution Using Microsoft Edge
Command:
```
python -m pytest -v --browser-channel msedge
```

Result:
```
68 passed, 3 warnings
```

## UI Scenarios Covered
1. Fiction and Non-Fiction category controls are available.
2. Non-Fiction shows the four filter groups (Book Format, Language, Publication Date, Customer Reviews) and their options.
3. Language filter (English) shows only matching books.
4. Format + Language combination (hardcover + English) shows only books matching both.
5. Customer Reviews minimum rating (4 stars and above) shows only books at or above the rating.
6. Publication Date (last year) shows only books within the window, including the boundary books.
7. Clear Filters resets the advanced filters, keeps the selected category, and shows the full category list again.
8. Filters selected under Fiction persist when switching to Non-Fiction, and the same controls and filtering behavior work in both categories.

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
All 68 automated tests (60 API/backend and 8 Playwright UI) pass when executed using the installed Microsoft Edge browser channel (`--browser-channel msedge`). Running `python -m pytest -v` without the channel option reports 60 passed and 8 errors in this environment, solely because the Playwright Chromium binary could not be downloaded. Running the UI tests in Playwright's bundled Chromium remains pending until it can be installed.
