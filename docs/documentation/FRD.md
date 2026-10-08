# Functional Requirements Document (FRD)

## Advanced Filtering for Non-Fiction Books

| | |
|---|---|
| **Jira story** | EPMCDMETST-68481 |
| **Enhancement** | Non-Fiction Books use the same advanced filtering as Fiction Books |
| **Document date** | 2026-10-08 |
| **Baseline** | `main` at `7ff461d` |
| **Status** | Draft for review |
| **Related documents** | [HLD](HLD.md), [LLD](LLD.md), [TRACEABILITY](TRACEABILITY.md) |

---

## 1. Evidence Basis and Limits

This FRD was written from the repository only. Read these limits before relying on it.

| # | Limit | Consequence |
|---|---|---|
| 1 | The Jira ticket was **not accessible** when the tests were validated (`docs/testing/test-validation-report.md` section 1). Its acceptance criteria were taken from the validation request, and the request text is not stored in the repository. | The requirements below are reconstructed from `README.md`, `PROJECT_STATUS.md`, the Gherkin feature and the implemented behavior. They are **not** a copy of the Jira acceptance criteria. |
| 2 | `docs/planning/` and `docs/design/` **do not exist** in the working tree or in any commit. | No planning or design document could be used as a source. Planning and design facts come from `README.md` ("Design notes"), `PROJECT_STATUS.md` and the commit history. |
| 3 | The requirement IDs `FR-01` to `FR-15` are labels created for this documentation package. | They are not Jira IDs. Use them only to link the four documents. |

## 2. Purpose

Describe the Non-Fiction advanced filtering enhancement delivered under EPMCDMETST-68481: what a customer can do, the rules the system applies, and how the behavior was verified.

## 3. Background

- Phase 1 (`ee70f2b`) delivered the catalog API, the Fiction and Non-Fiction categories, seed data and a basic browser UI. `GET /api/books` supported only a `category` filter.
- Phase 1's `PROJECT_STATUS.md` listed **"Advanced Non-Fiction filters"** as deferred work.
- Phase 2 (this story) delivered the advanced filters through `GET /api/books` and the browser UI (`dacb1e2`).
- Before `dacb1e2` the repository contained no advanced filtering for any category. The story describes Non-Fiction "the same as Fiction", and the delivered filters are available to both categories through one shared implementation.

## 4. Business Objective

From the Gherkin feature header (`docs/testing/gherkin-non-fiction-filtering.feature`):

> As a bookstore customer, I want to narrow the book list by format, language, publication date and customer reviews, so that I can find Non-Fiction books the same way I find Fiction books.

## 5. Scope

### 5.1 In scope

| Area | Description |
|---|---|
| Filters | Book Format, Language, Publication Date, Customer Reviews |
| Categories | Fiction and Non-Fiction (and All Books) use the same filters and behavior |
| API | Optional query parameters on `GET /api/books` |
| Browser UI | Four filter controls, a Clear Filters button, and result states |
| Validation | Unsupported filter values are rejected with HTTP 400 |
| Data | Seed data extended so every filter and boundary can be tested |

### 5.2 Not part of this enhancement

These are items the repository documents as deferred or as open observations. They are not implemented.

| Item | Source |
|---|---|
| CodeMie AI Assistant orchestration | `PROJECT_STATUS.md` (deferred) |
| Jira/Confluence integrations | `PROJECT_STATUS.md` (deferred) |
| Claude-Code workflow | `PROJECT_STATUS.md` (deferred) |
| Excluding future-dated books from publication windows | `test-validation-report.md` OBS-1 (decision pending) |
| Rejecting repeated query parameters | `test-validation-report.md` OBS-2 |
| Cancelling superseded browser requests | `test-validation-report.md` OBS-3 |

## 6. Users

One actor is described in the repository: the **bookstore customer** browsing the catalog in a web browser. No authentication, roles or accounts exist in the code.

## 7. Functional Requirements

"Evidence" shows how the requirement is verified. Test names and Gherkin scenarios are mapped in full in [TRACEABILITY.md](TRACEABILITY.md).

| ID | Requirement | Source | Evidence |
|---|---|---|---|
| **FR-01** | The customer can browse **All Books**, **Fiction Books** or **Non-Fiction Books**. Selecting Non-Fiction lists only Non-Fiction books. | Phase 1 behavior, kept by this story (Gherkin: regression scenarios) | API and UI tests, deployment check |
| **FR-02** | Every category shows four filter controls: **Book Format**, **Language**, **Publication Date**, **Customer Reviews**. Each has a default "Any" option plus the approved options listed in section 8. | Gherkin `@ui` "all four filter groups"; validation report section 1 | UI test, deployment UI check |
| **FR-03** | **Book Format** filter: hardcover, paperback, eBook, audiobook. Only books with the selected format are listed. | README "Filtering"; Gherkin | API and UI tests, deployment check |
| **FR-04** | **Language** filter: English, Spanish, French, German. Only books in the selected language are listed. | README "Filtering"; Gherkin | API and UI tests, deployment check |
| **FR-05** | **Publication Date** filter: last 30 days, last 6 months, last year. Only books published **on or after** the window's cutoff date are listed. | README; Gherkin filter semantics | API and UI tests, deployment check |
| **FR-06** | **Customer Reviews** filter: "3 stars and above" and "4 stars and above". The value is a **minimum** rating and is **inclusive** (a 3.0 book is in "3 and above"; a 2.9 book is not). | README "Design notes"; Gherkin | API and UI tests, deployment check |
| **FR-07** | Several filters can be active together and combine with **AND**. A book is listed only if it matches every active filter and the selected category. | Gherkin filter semantics | API and UI tests, deployment check |
| **FR-08** | An **empty** filter value means "no filter". | README; Gherkin filter semantics | API tests |
| **FR-09** | **Clear Filters** resets all four filters to their default and **keeps the selected category**, its tab, its heading, and shows the full list for that category. | Gherkin filter semantics; README | UI tests, API equivalent, deployment UI check |
| **FR-10** | Filter selections **persist when the customer switches category**. This is intentional, so the same filter set can be compared across categories. Only Clear Filters resets them. | README "Design notes" | UI tests |
| **FR-11** | Fiction and Non-Fiction behave identically for the same filter values (**parity**). | README; Gherkin `@parity` | API and UI tests |
| **FR-12** | Unsupported non-empty values for `category`, `format`, `language`, `publicationDate` or `minRating` are rejected with **HTTP 400** and a text `detail` message. Values are case-sensitive and not trimmed. | README; `PROJECT_STATUS.md` "Input validation" | API tests |
| **FR-13** | When no book matches, the page shows **"No books found."**. The list recovers after Clear Filters. | Gherkin `@no-results` | API and UI tests |
| **FR-14** | If the book request fails, the page shows **"Unable to load books. Please try again."** and an empty list. | Implemented in `frontend/app.js` | **Not tested** (listed as untested in the validation report) |
| **FR-15** | Existing behavior is unchanged: category-only listing, `GET /api/health`, `GET /api/books/{id}` (404 when missing), and HTTP 400 for an unknown category. | Gherkin `@regression`; `tests/test_books_api.py` | API tests |

## 8. Filter Reference

| Filter (UI label) | Query parameter | Allowed values | UI option labels |
|---|---|---|---|
| Category (tabs) | `category` | `Fiction`, `Non-Fiction` | All Books, Fiction Books, Non-Fiction Books |
| Book Format | `format` | `hardcover`, `paperback`, `eBook`, `audiobook` | Any, Hardcover, Paperback, eBook, Audiobook |
| Language | `language` | `English`, `Spanish`, `French`, `German` | Any, English, Spanish, French, German |
| Publication Date | `publicationDate` | `last30days`, `last6months`, `lastyear` | Any time, Last 30 days, Last 6 months, Last year |
| Customer Reviews | `minRating` | `3`, `4` | Any rating, 3 stars and above, 4 stars and above |

## 9. Business Rules

| ID | Rule |
|---|---|
| BR-1 | Filters combine with AND. |
| BR-2 | Publication windows include the cutoff date itself (on or after). |
| BR-3 | "Last 6 months" and "last year" use calendar-month arithmetic. If the target month is shorter, the day is clamped to the last day of that month (2026-08-31 minus 6 months is 2026-02-28). |
| BR-4 | The Customer Reviews value is a minimum, inclusive: `minRating=N` means `customer_rating >= N`. Only 3 and 4 are supported. |
| BR-5 | An empty value is "no filter". Any other unsupported value is an error (HTTP 400). |
| BR-6 | Values are case-sensitive (`eBook`, not `ebook`) and are not trimmed (`" English"` is invalid). |
| BR-7 | Clear Filters resets the four advanced filters only. The category is kept. |
| BR-8 | Filter selections persist across category changes. |

## 10. Data Requirements

- The existing `books` table already holds every field the filters need: `category`, `format`, `language`, `publication_date`, `customer_rating`.
- The customer-reviews value is stored in `customer_rating` (REAL, 0 to 5). The column was **deliberately not renamed** to `customer_reviews`.
- **No schema change and no migration** were required. Only the seed data was extended (18 books: 6 Fiction, 12 Non-Fiction), including "Mark" and "Just Past" books placed exactly on and one day before each publication cutoff.
- Seed dates are relative to the day the seed runs. Re-run `python -m scripts.seed` to refresh them.

Field-level detail is in [LLD.md](LLD.md).

## 11. Non-Functional Requirements and Constraints

Only items supported by the repository are listed.

| Area | Statement | Evidence |
|---|---|---|
| Security | Filter values are checked against fixed allow-lists and passed to SQL as bound parameters. SQL-injection style values are rejected with 400 and data is unchanged. | `app/filters.py`; API test |
| Test determinism | Tests run against a temporary seeded database with "today" frozen at 2026-08-31, so results do not depend on the run date. | `tests/conftest.py` |
| Maintainability | One shared query builder serves every category. There is no filters table. | `PROJECT_STATUS.md`; `app/filters.py` |
| Compatibility | The existing API, table and UI behavior are kept. | FR-15 |
| Runtime | Python 3.11+, FastAPI, SQLite, HTML/CSS/JavaScript, pytest. | `README.md` |

No performance, accessibility, responsive-layout or browser-compatibility requirement is stated in the repository, and none is claimed.

## 12. Acceptance Basis

Acceptance was verified with:

- **37 Gherkin scenarios** (17 outlines) in `docs/testing/gherkin-non-fiction-filtering.feature`: 27 tagged `@api`, 12 tagged `@ui`, 2 tagged both.
- **134 automated tests**: 115 API/unit/regression (pytest) and 19 Playwright UI tests. All passed in Microsoft Edge (`--browser-channel msedge`).
- Test validation result: **APPROVED** (`docs/testing/test-validation-report.md`).
- Local deployment result: **SUCCESS** (`docs/deployment/deployment-report.md`).

## 13. Assumptions, Limitations and Open Items

| # | Item | Source |
|---|---|---|
| 1 | Jira acceptance criteria were not available in the repository (section 1). | validation report |
| 2 | UI tests ran in **Microsoft Edge only**. Playwright's bundled Chromium could not be downloaded; Firefox and WebKit were not run. No other browser coverage is claimed. | `PROJECT_STATUS.md`; validation report section 9 |
| 3 | **OBS-1:** the date filter has no upper bound, so a future-dated book would appear in every publication window. Seed data has no future dates. | validation report |
| 4 | **OBS-2:** repeated query parameters are accepted and the last value is used. | validation report |
| 5 | **OBS-3:** the browser does not cancel earlier requests, so out-of-order results are possible on a slow network. Not reproduced. | validation report |
| 6 | UI interaction with every format and language option is not covered. Some values are covered through the API only. | validation report |
| 7 | The load-failure message (FR-14) has never been triggered in a test. | validation report |
| 8 | Not tested: accessibility, keyboard navigation, mobile layout, large data volumes, performance. | validation report |
| 9 | Selected filters are held in browser memory only. A page reload resets them (from `frontend/app.js`; not covered by a test). | `frontend/app.js` |

## 14. Source Evidence

| Artifact | Used for |
|---|---|
| `README.md` | Filter parameters, validation rules, design notes |
| `PROJECT_STATUS.md` | Phase 1 deferred item, Phase 2 status, known limitations |
| `docs/testing/gherkin-non-fiction-filtering.feature` | Filter semantics, scenarios |
| `docs/testing/test-validation-report.md` | Objective, coverage, observations, approval |
| `docs/testing/test-execution-report.md` | Test run results |
| `docs/deployment/deployment-report.md` | Deployment and build results |
| `app/`, `frontend/`, `scripts/` | Implemented behavior |
| Commits `dacb1e2`, `f8b12a7`, `1b61c63`, `7ff461d` | Delivery history |
