# Project Status

## Phase 1 — Application Foundation

Implemented:
- FastAPI backend
- SQLite database
- Book catalog API
- Fiction and Non-Fiction categories
- Seed data
- Basic browser UI
- API tests

## Phase 2 — Advanced Book Filtering (Jira EPMCDMETST-68481)

| Area | Status |
|---|---|
| Development | Done. Book Format, Language, Publication Date and Customer Reviews filters work for Fiction and Non-Fiction through `GET /api/books` and the browser UI. |
| Architecture / design | Done. One shared parameterized query builder (`app/filters.py`) serves both categories. The existing `customer_rating` column is reused; there is no filters table and no migration. |
| Input validation | Done. `format`, `language`, `publicationDate` and `minRating` (3 or 4) are validated; invalid non-empty values return HTTP 400, empty values mean "no filter". |
| API/unit testing | Done. 115 backend/API/unit tests pass. |
| UI automation | Done. 19 Playwright UI tests pass (run with Microsoft Edge via `--browser-channel msedge`). |
| Code review | Done. Review of commit dacb1e2 returned "approved with minor changes"; the approved changes are implemented in the follow-up work. |

Known limitations:
- Playwright UI tests have been run in Microsoft Edge only. Playwright's bundled Chromium could not be downloaded in the development environment, and Firefox/WebKit were not run.

Deferred to later capstone phases:
- CodeMie AI Assistant orchestration
- Jira/Confluence integrations
- Claude-Code workflow
- Build/deployment automation
- Documentation synchronization
