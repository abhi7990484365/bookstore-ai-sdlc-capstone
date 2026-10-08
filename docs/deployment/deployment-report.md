# Deployment Report - Local Deployment and Build

**Final deployment status: SUCCESS**

## 1. Summary

| Item | Value |
|---|---|
| Jira story | EPMCDMETST-68481 (advanced book filtering) |
| Deployment date | 2026-10-08 |
| Branch | `main` |
| Deployment target | Local machine (Windows 11 Enterprise) |
| Local application URL | http://127.0.0.1:8001 |
| API docs | http://127.0.0.1:8001/docs (HTTP 200) |

## 2. Commits

| Purpose | Commit | Message |
|---|---|---|
| Implementation | `dacb1e2` | feat: add advanced book filtering |
| Implementation (review fixes) | `f8b12a7` | fix: address code review findings for EPMCDMETST-68481 |
| Testing | `1b61c63` | test: add Gherkin scenarios and validation report for EPMCDMETST-68481 |

`1b61c63` was the latest commit (HEAD) of `main` when the deployment started. The working tree was clean at that point.

## 3. Environment

| Component | Version / detail |
|---|---|
| Python | 3.13.0 (project virtual environment `.venv`) |
| FastAPI | 0.142.4 |
| Uvicorn | 0.54.0 |
| Starlette | 1.7.0 |
| Pydantic | 2.13.5 |
| Database | SQLite (`bookstore.db`, gitignored) |
| Browser used for UI verification | Microsoft Edge (headless, via Playwright 1.63.0) |

## 4. Deployment method

The repository has no Dockerfile and no docker-compose file. Docker is also not installed on the machine, so the deployment followed the README's virtual-environment path:

1. Inspect the repository (`README.md`, `requirements.txt`, `app/main.py`, `app/routes/books.py`, `app/filters.py`, `app/database.py`, `scripts/seed.py`, `frontend/`).
2. `python -m pip install -r requirements.txt` (run with `.venv`) - all requirements were already satisfied.
3. `python -m scripts.seed` - output: `Seeded 18 books.`
4. `python -m uvicorn app.main:app --host 127.0.0.1 --port 8001` - the server started and application startup completed.

No application code was modified. No build step is needed to run the application.

## 5. Build

| Item | Value |
|---|---|
| Build command | `python scripts/build.py` |
| Build script | `scripts/build.py` (standard library only) |
| Artifact | `dist/bookstore-ai-sdlc-capstone.zip` |
| Artifact size | 29,675 bytes |
| SHA-256 | `fac352be45f8a08bacac469c2163f371bee8a08fb341eb1fd0277effd8f08962` |
| Files included | 24 |
| Build result | BUILD SUCCESS (exit code 0) |

Contents: `app/`, `frontend/`, `scripts/`, `tests/`, `docs/`, `requirements.txt`, `README.md`, `.gitignore` and `PROJECT_STATUS.md`.

Excluded: `.git/`, `.venv/`, `venv/`, `__pycache__/`, `*.pyc`, `bookstore.db`, `.idea/`, `.claude/`, `.codemie/`, `dist/`. The script also excludes `.pytest_cache/`, `*.pyo`, `*.sqlite` and `.env`.

### Build verification
- **Determinism:** the build was run twice and both runs produced the identical SHA-256 shown above. Entries are sorted and use fixed timestamps (1980-01-01), fixed permissions and fixed compression settings.
- **Integrity:** `zipfile.testzip()` returned no errors.
- **Listing:** the archive opened and listed 24 entries with both Python `zipfile` and .NET `System.IO.Compression`.
- **Exclusions:** a scan of the entry names found none of the excluded paths or patterns.
- **Extracted copy:** the ZIP was extracted to a fresh temporary directory. `python -m scripts.seed` there reported `Seeded 18 books.` and `pytest --ignore=tests/ui` reported **115 passed, 3 warnings**. The UI tests (`tests/ui`) were not run on the extracted copy.

## 6. API verification

Base URL: `http://127.0.0.1:8001`

| # | Request | HTTP | Result |
|---|---|---|---|
| 1 | `GET /api/health` | 200 | `{"status":"ok"}` |
| 2 | `GET /api/books` | 200 | 18 books (6 Fiction, 12 Non-Fiction) |
| 3 | `GET /api/books?category=Non-Fiction` | 200 | 12 books, all Non-Fiction |
| 4 | `GET /api/books?category=Non-Fiction&format=hardcover` | 200 | 4 books: ids 31, 35, 41, 42 |
| 5 | `GET /api/books?category=Non-Fiction&minRating=4` | 200 | 3 books: ids 31, 32, 34 |
| 6 | `GET /api/books?category=Non-Fiction&language=English` | 200 | 4 books: ids 31, 35, 37, 38 |
| 7 | `GET /api/books?category=Non-Fiction&publicationDate=last30days` | 200 | 3 books: ids 31, 34, 37 |
| 8 | `GET /api/books?category=Non-Fiction&format=hardcover&publicationDate=lastyear&minRating=4` | 200 | 1 book: "History of Modern Cities" (id 31) |
| 9 | `GET /api/books?category=Non-Fiction&format=pdf` | 400 | `{"detail":"Unsupported format"}` |

### Result details
- **Health endpoint:** returned HTTP 200 with `{"status":"ok"}`.
- **Books API:** returned HTTP 200 with all 18 seeded books.
- **Non-Fiction filtering:** returned the 12 Non-Fiction books and no Fiction books.
- **Advanced filtering:** the `format`, `minRating`, `language` and `publicationDate` filters each returned the expected subset of Non-Fiction books, and the counts match the seed data.
- **Combined AND filtering:** `category=Non-Fiction` AND `format=hardcover` AND `publicationDate=lastyear` AND `minRating=4` returned only "History of Modern Cities". It is the only Non-Fiction hardcover book published on or after 2025-10-08 with a rating of at least 4 (4.7).
- **Invalid-filter handling:** `format=pdf` returned HTTP 400 with `Unsupported format`.

## 7. Browser UI verification

Automated with Playwright through headless Microsoft Edge against `http://127.0.0.1:8001/`. The throwaway script was kept outside the repository. A screenshot was saved to the temporary directory.

| Check | Result |
|---|---|
| Page loads | PASS - HTTP 200, title "Online Bookstore", heading "Online Bookstore" |
| All Books tab | PASS - 18 book cards |
| Non-Fiction tab | PASS - section title "Non-Fiction Books", 12 book cards |
| Non-Fiction advanced filters available | PASS - Book Format, Language, Publication Date and Customer Reviews are all visible and enabled |
| Filter options | PASS - format: hardcover, paperback, eBook, audiobook; language: English, Spanish, French, German; publication date: last30days, last6months, lastyear; reviews: 3, 4 |
| Clear Filters button | PASS - visible |
| Non-Fiction + Hardcover | PASS - 4 cards |
| Non-Fiction + Hardcover + Last year + 4 stars and above | PASS - 1 card, "History of Modern Cities" |
| Clear Filters | PASS - returns to 12 cards and stays on Non-Fiction |
| Console and page errors | One error: HTTP 404 on `/favicon.ico` (see section 8) |

## 8. Deviations, warnings and limitations

1. **Port 8001 instead of 8000.** Port 8000 was already in use by another instance of this same application (PID 13004, started with `uvicorn app.main:app --host 127.0.0.1 --port 8000`), which also answered `/api/health`. It was not started in this session and was left running. This deployment used port 8001, so the README's default URL (`http://127.0.0.1:8000`) does not point at this deployment. The code version of the instance on port 8000 was not verified.
2. **Docker unavailable.** No Dockerfile or docker-compose file exists in the repository, and the `docker` command is not installed on the machine. A container-based deployment could not be used or tested.
3. **`/favicon.ico` returns 404 (cosmetic).** The browser requests a favicon, and the application has no route for one. The server log shows `GET /favicon.ico ... 404 Not Found`. It is the only console error and has no effect on functionality.
4. **Database re-seeded.** `python -m scripts.seed` ran `DELETE FROM books` and re-inserted 18 rows in `bookstore.db`. The file is gitignored. Seed dates are relative to the run date (2026-10-08). The application on port 8000 reads the same database file.
5. **Test warnings.** The extracted-copy test run reported 3 warnings, including a FastAPI `on_event` deprecation warning.
6. **Browser.** Playwright's bundled Chromium was not used. The installed Microsoft Edge was used instead.

## 9. Repository state at time of writing

- Nothing has been committed in this deployment session.
- Uncommitted changes: `scripts/build.py` (new), `.gitignore` (added a `dist/` entry so the build artifact is not committed) and this report.
- The generated ZIP in `dist/` is gitignored.
- No application code was modified.

## 10. Final status

**SUCCESS.** The application was deployed locally at **http://127.0.0.1:8001**. Every API check and browser UI check passed, the build produced a verified, reproducible ZIP artifact, and the deviations in section 8 are documented.
