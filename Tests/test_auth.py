REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"

USER = {"email": "user@test.com", "password": "secret123"}


async def test_register_returns_token_pair(client):
    resp = await client.post(REGISTER, json=USER)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_email(client):
    await client.post(REGISTER, json=USER)
    resp = await client.post(REGISTER, json=USER)
    assert resp.status_code == 409


async def test_login_success(client):
    await client.post(REGISTER, json=USER)
    resp = await client.post(LOGIN, json=USER)
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert "refresh_token" in resp.json()


async def test_login_wrong_password(client):
    await client.post(REGISTER, json=USER)
    resp = await client.post(LOGIN, json={**USER, "password": "wrongpass"})
    assert resp.status_code == 401


async def test_login_unknown_email(client):
    resp = await client.post(LOGIN, json={"email": "nobody@test.com", "password": "pass"})
    assert resp.status_code == 401


async def test_refresh_returns_new_token_pair(client):
    reg = (await client.post(REGISTER, json=USER)).json()
    resp = await client.post(REFRESH, json={"refresh_token": reg["refresh_token"]})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["refresh_token"] != reg["refresh_token"]


async def test_refresh_rotates_token(client):
    reg = (await client.post(REGISTER, json=USER)).json()
    old_token = reg["refresh_token"]
    await client.post(REFRESH, json={"refresh_token": old_token})
    resp = await client.post(REFRESH, json={"refresh_token": old_token})
    assert resp.status_code == 401


async def test_refresh_invalid_token(client):
    resp = await client.post(REFRESH, json={"refresh_token": "not-a-real-token"})
    assert resp.status_code == 401


async def test_logout_invalidates_refresh_token(client):
    reg = (await client.post(REGISTER, json=USER)).json()
    refresh_token = reg["refresh_token"]

    assert (await client.post(LOGOUT, json={"refresh_token": refresh_token})).status_code == 204
    assert (await client.post(REFRESH, json={"refresh_token": refresh_token})).status_code == 401


async def test_logout_idempotent(client):
    resp = await client.post(LOGOUT, json={"refresh_token": "nonexistent-token"})
    assert resp.status_code == 204
