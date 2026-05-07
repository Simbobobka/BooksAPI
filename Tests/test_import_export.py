import json

IMPORT = "/api/v1/books/import"
EXPORT = "/api/v1/books/export"

_BOOKS_JSON = [
    {
        "title": "Import One",
        "published_year": 2020,
        "genre_id": 1,
        "authors": [{"name": "Alice", "last_name": "Smith"}],
    },
    {
        "title": "Import Two",
        "published_year": 2021,
        "genre_id": 2,
        "authors": [{"name": "Bob", "last_name": "Jones"}],
    },
]

_CSV_TWO_BOOKS = (
    "title,published_year,genre_id,author_name,author_last_name,author_middle_name,author_pen_name\n"
    "CSV One,2020,1,Alice,Smith,,\n"
    "CSV Two,2021,2,Bob,Jones,,\n"
)

_CSV_MULTI_AUTHOR = (
    "title,published_year,genre_id,author_name,author_last_name,author_middle_name,author_pen_name\n"
    "Co-Written,2020,1,Alice,Smith,,\n"
    "Co-Written,2020,1,Bob,Jones,,\n"
)


async def test_import_json_success(client, auth_headers):
    content = json.dumps(_BOOKS_JSON).encode()
    resp = await client.post(
        IMPORT, files={"file": ("books.json", content, "application/json")}, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 2
    assert data["failed"] == 0
    assert data["errors"] == []


async def test_import_json_invalid_genre(client, auth_headers):
    bad = [{"title": "Bad", "published_year": 2020, "genre_id": 99999, "authors": [{"name": "X"}]}]
    resp = await client.post(
        IMPORT,
        files={"file": ("books.json", json.dumps(bad).encode(), "application/json")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 0
    assert data["failed"] == 1
    assert data["errors"][0]["row"] == 1


async def test_import_json_partial_success(client, auth_headers):
    mixed = [_BOOKS_JSON[0], {"title": "Bad", "published_year": 2020, "genre_id": 99999, "authors": [{"name": "X"}]}]
    resp = await client.post(
        IMPORT,
        files={"file": ("books.json", json.dumps(mixed).encode(), "application/json")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 1
    assert data["failed"] == 1


async def test_import_json_unauthenticated(client):
    resp = await client.post(
        IMPORT, files={"file": ("books.json", b"[]", "application/json")}
    )
    assert resp.status_code == 401


async def test_import_csv_success(client, auth_headers):
    resp = await client.post(
        IMPORT,
        files={"file": ("books.csv", _CSV_TWO_BOOKS.encode(), "text/csv")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["imported"] == 2


async def test_import_csv_multi_author_grouping(client, auth_headers):
    resp = await client.post(
        IMPORT,
        files={"file": ("books.csv", _CSV_MULTI_AUTHOR.encode(), "text/csv")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 1

    books_resp = await client.get("/api/v1/books/", params={"title": "Co-Written"})
    book = books_resp.json()["items"][0]
    assert len(book["authors"]) == 2


async def test_export_json(client, book):
    resp = await client.get(EXPORT, params={"format": "json"})
    assert resp.status_code == 200
    assert resp.headers["content-disposition"] == "attachment; filename=books.json"
    books = json.loads(resp.content)
    assert isinstance(books, list)
    assert any(b["id"] == book["id"] for b in books)


async def test_export_csv(client, book):
    resp = await client.get(EXPORT, params={"format": "csv"})
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert str(book["id"]) in resp.text
    assert "author_name" in resp.text


async def test_export_filter_by_genre(client, auth_headers):
    await client.post(
        "/api/v1/books/",
        json={"title": "Genre Filter Book", "published_year": 2020, "genre_id": 8, "authors": [{"name": "X"}]},
        headers=auth_headers,
    )
    resp = await client.get(EXPORT, params={"format": "json", "genre_id": 8})
    assert resp.status_code == 200
    books = json.loads(resp.content)
    assert all(b["genre"]["id"] == 8 for b in books)
