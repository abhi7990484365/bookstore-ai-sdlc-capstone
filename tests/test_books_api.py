def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_list_books(client):
    response = client.get("/api/books")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_nonfiction_category(client):
    response = client.get("/api/books?category=Non-Fiction")
    assert response.status_code == 200
    assert response.json()
    assert all(book["category"] == "Non-Fiction" for book in response.json())

def test_invalid_category(client):
    assert client.get("/api/books?category=Unknown").status_code == 400

def test_missing_book(client):
    assert client.get("/api/books/999999").status_code == 404
