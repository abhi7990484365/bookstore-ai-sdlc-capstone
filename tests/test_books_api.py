from fastapi.testclient import TestClient
from app.main import app
from app.database import initialize_database

client = TestClient(app)

def setup_module():
    initialize_database()

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_list_books():
    response = client.get("/api/books")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_nonfiction_category():
    response = client.get("/api/books?category=Non-Fiction")
    assert response.status_code == 200
    assert response.json()
    assert all(book["category"] == "Non-Fiction" for book in response.json())

def test_invalid_category():
    assert client.get("/api/books?category=Unknown").status_code == 400

def test_missing_book():
    assert client.get("/api/books/999999").status_code == 404
