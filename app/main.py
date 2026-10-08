from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.database import initialize_database
from app.routes.books import router as books_router

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND = BASE_DIR / "frontend"

app = FastAPI(
    title="Bookstore AI SDLC Capstone",
    version="0.1.0",
    description="Online bookstore foundation for the CodeMie capstone.",
)

@app.on_event("startup")
def startup():
    initialize_database()

@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}

app.include_router(books_router)

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(FRONTEND / "index.html")

@app.get("/app.js", include_in_schema=False)
def javascript():
    return FileResponse(FRONTEND / "app.js", media_type="application/javascript")

@app.get("/styles.css", include_in_schema=False)
def stylesheet():
    return FileResponse(FRONTEND / "styles.css", media_type="text/css")
