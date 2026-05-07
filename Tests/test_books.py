import pytest

BOOKS = "/api/v1/books/"


def _payload(**kwargs):
    base = {
        "title": "Default Book",
        "published_year": 2020,
        "genre_id": 1,
        "authors": [{"name": "Default", "last_name": "Author"}],
    }
    return {**base, **kwargs}


async def test_create_book(client, auth_headers):
    resp = await client.post(BOOKS, json=_payload(title="Clean Code"), headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Clean Code"
    assert data["authors"][0]["last_name"] == "Author"
    assert "id" in data


async def test_create_book_unauthenticated(client):
    resp = await client.post(BOOKS, json=_payload())
    assert resp.status_code == 401


async def test_create_book_invalid_genre(client, auth_headers):
    resp = await client.post(BOOKS, json=_payload(genre_id=99999), headers=auth_headers)
    assert resp.status_code == 404


async def test_create_book_multiple_authors(client, auth_headers):
    payload = _payload(
        authors=[
            {"name": "Terry", "last_name": "Pratchett"},
            {"name": "Neil", "last_name": "Gaiman"},
        ]
    )
    resp = await client.post(BOOKS, json=payload, headers=auth_headers)
    assert resp.status_code == 201
    assert len(resp.json()["authors"]) == 2


async def test_get_book(client, book):
    resp = await client.get(f"{BOOKS}{book['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == book["id"]


async def test_get_book_not_found(client):
    resp = await client.get(f"{BOOKS}999999")
    assert resp.status_code == 404


async def test_list_books_returns_created(client, book):
    resp = await client.get(BOOKS)
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert any(b["id"] == book["id"] for b in data["items"])


async def test_list_books_filter_by_title(client, auth_headers):
    await client.post(BOOKS, json=_payload(title="Unique XYZ Title"), headers=auth_headers)
    resp = await client.get(BOOKS, params={"title": "Unique XYZ"})
    assert resp.status_code == 200
    assert all("unique xyz" in b["title"].lower() for b in resp.json()["items"])


async def test_list_books_filter_by_genre(client, book):
    resp = await client.get(BOOKS, params={"genre_id": book["genre"]["id"]})
    assert resp.status_code == 200
    assert all(b["genre"]["id"] == book["genre"]["id"] for b in resp.json()["items"])


async def test_list_books_pagination(client, auth_headers):
    for i in range(3):
        await client.post(BOOKS, json=_payload(title=f"Paginated Book {i}"), headers=auth_headers)
    resp = await client.get(BOOKS, params={"limit": 2, "offset": 0})
    assert resp.status_code == 200
    assert len(resp.json()["items"]) <= 2


async def test_update_book_title(client, book, auth_headers):
    resp = await client.patch(
        f"{BOOKS}{book['id']}", json={"title": "Updated Title"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"


async def test_update_book_unauthenticated(client, book):
    resp = await client.patch(f"{BOOKS}{book['id']}", json={"title": "Hack"})
    assert resp.status_code == 401


async def test_update_book_not_found(client, auth_headers):
    resp = await client.patch(f"{BOOKS}999999", json={"title": "X"}, headers=auth_headers)
    assert resp.status_code == 404


async def test_delete_book(client, auth_headers):
    b = (await client.post(BOOKS, json=_payload(), headers=auth_headers)).json()
    assert (await client.delete(f"{BOOKS}{b['id']}", headers=auth_headers)).status_code == 204
    assert (await client.get(f"{BOOKS}{b['id']}")).status_code == 404


async def test_delete_book_unauthenticated(client, book):
    resp = await client.delete(f"{BOOKS}{book['id']}")
    assert resp.status_code == 401


async def test_delete_book_not_found(client, auth_headers):
    resp = await client.delete(f"{BOOKS}999999", headers=auth_headers)
    assert resp.status_code == 404


async def test_recommendations_same_genre(client, auth_headers):
    b1 = (await client.post(BOOKS, json=_payload(title="Rec A", genre_id=6), headers=auth_headers)).json()
    b2 = (await client.post(BOOKS, json=_payload(title="Rec B", genre_id=6), headers=auth_headers)).json()

    resp = await client.get(f"{BOOKS}{b1['id']}/recommendations")
    assert resp.status_code == 200
    assert any(r["id"] == b2["id"] for r in resp.json())


async def test_recommendations_shared_author(client, auth_headers):
    author = {"name": "Shared", "last_name": "Writer"}
    b1 = (await client.post(BOOKS, json=_payload(title="SA Book 1", genre_id=1, authors=[author]), headers=auth_headers)).json()
    b2 = (await client.post(BOOKS, json=_payload(title="SA Book 2", genre_id=2, authors=[author]), headers=auth_headers)).json()

    resp = await client.get(f"{BOOKS}{b1['id']}/recommendations")
    assert resp.status_code == 200
    assert any(r["id"] == b2["id"] for r in resp.json())


async def test_recommendations_not_found(client):
    resp = await client.get(f"{BOOKS}999999/recommendations")
    assert resp.status_code == 404
