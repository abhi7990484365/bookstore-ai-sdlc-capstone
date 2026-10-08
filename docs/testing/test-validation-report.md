# Test Validation Report

| | |
|---|---|
| **Jira story** | EPMCDMETST-68481 |
| **Enhancement** | Non-Fiction Books use the same advanced filtering as Fiction |
| **Implementation commit** | `dacb1e2` (feat: add advanced book filtering) |
| **Code review / fix commit** | `f8b12a7` (fix: address code review findings) |
| **Branch** | `main` |
| **Validation date** | 2026-10-08 |
| **Result** | **APPROVED** |

## 1. Test Objective

Validate that Non-Fiction Books support the same advanced filtering as Fiction Books, through both the API (`GET /api/books`) and the browser UI:

- Book Format: hardcover, paperback, eBook, audiobook
- Language: English, Spanish, French, German
- Publication Date: last 30 days, last 6 months, last year
- Customer Reviews: 4 stars and above, 3 stars and above

Also validate single filters, multiple filters combined with AND logic, Clear Filters, category preservation after clearing, Fiction and Non-Fiction parity, invalid input handling, API behavior, Playwright UI behavior, and regression coverage.

Limitation: the acceptance criteria were taken from the validation request. The Jira ticket itself was not accessible in this session.

## 2. Test Environment

| Item | Value |
|---|---|
| OS | Windows 11 Enterprise |
| Python | 3.13.0 |
| Backend | FastAPI 0.142.4, Starlette 1.7.0, Uvicorn 0.54.0, SQLite |
| Test tools | pytest 9.1.1, pytest-playwright 0.9.0, Playwright 1.63.0, httpx 0.28.1 |
| UI browser | Microsoft Edge, via `--browser-channel msedge` |
| Test data | Temporary seeded SQLite database (`scripts/seed.py`, 18 books), current date frozen at 2026-08-31 |
| UI server | The real application served in-process on a free local port, using the same database and frozen date |

## 3. Test Approach

1. Gherkin scenarios were written first from the story requirements, before any test was executed (`docs/testing/gherkin-non-fiction-filtering.feature`).
2. The existing pytest and Playwright suites were inspected and mapped to those scenarios.
3. The unchanged application was tested with the existing framework. No application code was modified.
4. Expected results are independent of the filter code under test:
   - UI tests derive expectations from the seed definition and hardcoded date cutoffs.
   - API tests compare against the unfiltered list filtered in Python.
5. Two extra checks were run outside the repository, on a temporary copy or temporary database, to test the quality of the suite:
   - **Mutation checks:** 11 deliberate breakages of the filter logic or UI code, to confirm the tests fail when the behavior is wrong.
   - **Real-clock exploratory probes:** a temporary database seeded with the real date instead of the frozen date.

## 4. Gherkin Coverage

File: `docs/testing/gherkin-non-fiction-filtering.feature`. Scenarios are tagged `@api` or `@ui` to show which automated layer covers them.

| Area | Gherkin coverage |
|---|---|
| Non-Fiction category | Filter groups and options shown; category-only results |
| Book Format | All 4 formats, Non-Fiction and Fiction; browser selection |
| Language | All 4 languages, Non-Fiction and Fiction; browser selection |
| Publication Date | 3 windows, both categories; inclusive boundary books; nested windows; month-end clamping |
| Customer Reviews | 3+ and 4+ in both categories; inclusive boundaries; browser selection |
| Single filter | Format, Language, Publication Date and Customer Reviews each individually |
| Multiple filters (AND) | Format and Language in UI; documented 4-filter example; 4 filters across both categories; narrowing check |
| Clear Filters | Reset of all four filters with the category preserved (UI, Fiction and Non-Fiction); API equivalent |
| Fiction and Non-Fiction behavior | Same controls, same results, selections persist on category switch (both directions) |
| Invalid format | Invalid values, with and without category; valid values accepted with exact spelling |
| Invalid language | Invalid values, with and without category; valid values accepted with exact spelling |
| Invalid rating | Non-numeric, decimal, out-of-range and unsupported values |
| Empty / no results and recovery | Empty API list; "No books found." in the UI; recovery after Clear Filters |
| Regression | Category-only behavior unchanged; empty filter values mean no filter |

## 5. API Test Coverage

Files: `tests/test_books_api.py` (5 tests) and `tests/test_books_filters.py` (110 tests). Together they make **115 API, unit and regression tests**, all passing.

- **Format:** all 4 values in both categories, plus exact-spelling acceptance.
- **Language:** all 4 values in both categories, plus exact-spelling acceptance.
- **Publication Date:** 3 windows in both categories. Boundary books sit exactly on and one day before each cutoff. Windows are nested. Cutoffs are checked against literal frozen dates, including month-end clamping (Aug 31 to Feb 28) and a leap-year case.
- **Customer Reviews:** 3 and 4 in both categories. Boundaries are inclusive (3.0 in 3+, 2.9 out, 4.0 in 4+).
- **AND logic:** documented example (`History of Modern Cities`), all four filters in both categories, and narrowing of single-filter results.
- **Clear behavior:** a category-only request restores the full category list.
- **Parity:** the same filter values behave identically for Fiction and Non-Fiction.
- **Empty and no results:** empty filter values are ignored; a no-match combination returns an empty list.
- **Existing API:** health returns 200, an invalid category returns 400, a missing book returns 404.

## 6. UI Test Coverage

File: `tests/ui/test_book_filters_ui.py`. **19 Playwright tests**, run in Microsoft Edge, all passing.

1. Fiction and Non-Fiction category controls are available.
2. Non-Fiction shows all four filter groups with the approved option lists.
3. Single filter: Language English (Non-Fiction).
4. Multiple filters: hardcover and English combine with AND (Non-Fiction).
5. Customer Reviews 4 stars and above (Non-Fiction).
6. Customer Reviews 3 stars and above (Fiction).
7. Publication Date last 30 days, last 6 months and last year in Non-Fiction, each checking the inside and outside boundary books (3 tests).
8. Publication Date last 30 days, last 6 months and last year in Fiction (3 tests).
9. Publication Date windows are nested.
10. Clear Filters resets all four filters and keeps the category, active tab, heading and list, for Fiction and Non-Fiction (2 tests).
11. Filters persist when switching category, Fiction to Non-Fiction and Non-Fiction to Fiction (2 tests).
12. Filters work the same in Fiction and Non-Fiction.
13. No-results state ("No books found.") and recovery after Clear Filters.

## 7. Negative Test Coverage

All executed at the API level and all passing.

| Input | Values tested | Expected | Result |
|---|---|---|---|
| Invalid format | `pdf`, `ebook`, `EBOOK`, `Hardcover`, `" hardcover"`, `"hardcover "`, `x`, each with no category, Fiction and Non-Fiction | HTTP 400, text `detail` | Pass |
| Invalid language | `Klingon`, `english`, `ENGLISH`, `" English"`, `"English "`, `x`, each with no category, Fiction and Non-Fiction | HTTP 400, text `detail` | Pass |
| Invalid rating | `abc`, `3.5`, `0`, `-1`, `5` (plus `2` in the combined invalid-values test) | HTTP 400, text `detail` | Pass |
| Invalid publication window | `lastcentury` | HTTP 400 | Pass |
| Invalid category | `Unknown` | HTTP 400 | Pass |
| Invalid value mixed with valid filters | Fiction, hardcover and `minRating=abc` | HTTP 400 | Pass |
| SQL-injection style values | `x' OR '1'='1` in format; `x'; DROP TABLE books;--` in language | HTTP 400, data unchanged | Pass |
| Empty values | All filter parameters empty | Treated as no filter | Pass |

## 8. Test Execution Results

| Run | Command | Passed | Failed | Errors |
|---|---|---|---|---|
| API, unit and regression only | `python -m pytest tests --ignore=tests/ui` | 115 | 0 | 0 |
| Full suite, default browser | `python -m pytest` | 115 | 0 | 19 (environmental, see section 9) |
| **Full suite, Microsoft Edge** | `python -m pytest -v --browser-channel msedge` | **134** | **0** | **0** |

**Edge result: 134 passed / 0 failed** (115 API/unit/regression and 19 Playwright UI tests), completed in about 19 seconds with 3 warnings.

The 3 warnings are existing deprecation warnings:
- httpx with `starlette.testclient`
- `on_event` in `app/main.py:16`
- `on_event` in `fastapi/applications.py`

None are Playwright warnings and none are related to this story.

### Additional quality checks (outside the repository)

- **Mutation checks, 11 mutants:** the test suite failed for each of these deliberate breakages:
  - AND changed to OR
  - publication boundary made exclusive
  - rating boundary made exclusive
  - 30 days changed to 31
  - language filter ignored
  - format validation removed
  - `minRating=5` allowed
  - Clear Filters wiping the category
  - Clear Filters not resetting the dropdowns
  - rating parameter not sent from the UI
  - filters hidden for Non-Fiction
  - One mutant (hiding the filters with the `hidden` attribute) did not fail the suite. The cause was that the stylesheet's `display:flex` overrides `hidden`, so the change had no visible effect. Redone with `display:none`, the suite failed (4 failed, 130 passed).
- **Real-clock probe:** with a temporary database seeded with the real date (2026-10-08), the filters returned expected results.

## 9. Chromium Environmental Limitation

Running `python -m pytest` without `--browser-channel msedge` produces **115 passed, 19 errors**. All 19 errors are the Playwright UI tests failing at browser launch:

```
BrowserType.launch: Executable doesn't exist at
C:\Users\AbhiVijaybhaiVachhan\AppData\Local\ms-playwright\chromium_headless_shell-1243\chrome-headless-shell-win64\chrome-headless-shell.exe
```

- This is an environment problem, not a product or test defect. Playwright's bundled Chromium is not installed on this machine, and a previous attempt to download it timed out (see `docs/testing/test-execution-report.md`).
- Microsoft Edge, already installed on the machine, was used through Playwright's `msedge` channel, and all UI tests passed there.
- pytest labels the UI tests `[chromium]` because Edge is driven through Playwright's `chromium` browser type. They ran in Edge.
- No results were obtained with Playwright's bundled Chromium, Firefox or WebKit, and none are claimed.

## 10. Defects and Risks

### Defects

No blocking or functional defects were found. Low-severity observations:

| ID | Severity | Observation |
|---|---|---|
| OBS-1 | Low | **Future-dated books appear in every publication window.** The date filter has no upper bound. A book dated 400 days ahead, injected into a temporary database, appeared under "Last 30 days". The seed data has no future dates, so this is not currently visible. |
| OBS-2 | Low | **Repeated query parameters are accepted.** `?format=pdf&format=hardcover` returns 200 and the last value is used instead of an error. |
| OBS-3 | Low | **Stale UI results are possible.** `frontend/app.js` does not cancel earlier requests, so on a slow network rapid filter changes could show out-of-order results. This was not reproduced or tested. |

### Risks

| Risk | Impact | Mitigation |
|---|---|---|
| UI tests have only run in Edge | Browser-specific problems in other browsers would not be detected | Install Playwright Chromium or run the UI tests in CI |
| UI coverage is narrower than API coverage | Some format and language values (for example audiobook and French) are verified through the API only | Add UI tests for the remaining options |
| Small seed data (18 books) | Many results contain only 1 to 3 books, so the boundary and AND tests depend on the specially added "Mark" and "Just Past" books | Use larger or more varied test data |
| Default `python -m pytest` reports 19 errors on this machine | Can be mistaken for failures | Document the `--browser-channel msedge` command, or install Chromium |

## 11. Untested Areas

- Playwright's bundled Chromium, Firefox and WebKit.
- The UI error state ("Unable to load books. Please try again.") when the API returns an error. It was never triggered.
- UI interaction with every format and language option. Only some values are exercised in the UI.
- Request cancellation and out-of-order responses under slow or fast-changing network conditions.
- Future-dated books, and books with missing or malformed `publication_date` values.
- Large data volumes and performance.
- Accessibility, keyboard navigation, mobile and responsive layouts.
- Security testing beyond input validation and SQL-injection style values.
- Jira ticket text: acceptance criteria were taken from the validation request.
- The existing `docs/testing/test-execution-report.md` was not edited as part of this validation.

## 12. Final Recommendation

**APPROVED.**

All 134 automated tests pass in Microsoft Edge with 0 failures. Every requested filter, combination, Clear Filters and category-preservation behavior, Fiction and Non-Fiction parity case, invalid input case and no-results recovery was verified, and 11 deliberate breakages of the filter logic were caught by the suite. The only open items are the low-severity observations above and the missing Chromium binary in this environment. None of them block the story.

Recommended follow-ups, not required for approval:
1. Install Playwright Chromium, or run the UI tests in CI, so the default `python -m pytest` command passes.
2. Decide whether future-dated books should be excluded from publication windows.
3. Add UI tests for the load-failure state and for the remaining format and language values.
