async def test_list_genres_returns_seeded_data(client):
    resp = await client.get("/api/v1/genres/")
    assert resp.status_code == 200
    genres = resp.json()
    assert len(genres) >= 10
    names = {g["name"] for g in genres}
    assert "Fiction" in names
    assert "Fantasy" in names


async def test_list_genres_shape(client):
    resp = await client.get("/api/v1/genres/")
    for genre in resp.json():
        assert "id" in genre
        assert "name" in genre
