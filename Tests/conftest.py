import os
from pathlib import Path

os.environ["DATABASE_URL"] = "postgresql://books:books@localhost:5432/books"

import pytest
import asyncpg
from httpx import ASGITransport, AsyncClient

from App.Api.Limiter import limiter
from App.Api.V1.Dependencies.GetDbConnection import get_db_connection
from App.Config.Settings import get_settings
from App.Db.ConnectionPool import ConnectionPool
from App.Db.MigrationRunner import MigrationRunner
from App.Main import app

get_settings.cache_clear()

MIGRATIONS_DIR = Path(__file__).parent.parent / "App" / "Db" / "Migrations"


@pytest.fixture(scope="session", autouse=True)
async def apply_migrations():
    settings = get_settings()
    pool = ConnectionPool(settings.database_url)
    await pool.connect()
    await MigrationRunner(pool, MIGRATIONS_DIR).run()
    await pool.close()


@pytest.fixture(autouse=True)
def reset_rate_limits():
    limiter._storage.reset()


@pytest.fixture
async def db_connection():
    conn = await asyncpg.connect(get_settings().database_url)
    tr = conn.transaction()
    await tr.start()
    yield conn
    await tr.rollback()
    await conn.close()


@pytest.fixture
async def client(db_connection):
    async def override():
        yield db_connection

    app.dependency_overrides[get_db_connection] = override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "tester@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def book(client, auth_headers):
    resp = await client.post(
        "/api/v1/books/",
        json={
            "title": "Test Book",
            "published_year": 2020,
            "genre_id": 1,
            "authors": [{"name": "Test", "last_name": "Author"}],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()
