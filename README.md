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
python -m scripts.seed.py
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000
API docs: http://127.0.0.1:8000/docs

Advanced Non-Fiction filtering is intentionally deferred to the enhancement phase.
