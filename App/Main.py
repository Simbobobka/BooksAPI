from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from App.Api.Limiter import limiter
from App.Api.V1.Router import router as v1_router
from App.Config.Settings import get_settings
from App.Db.ConnectionPool import ConnectionPool
from App.Db.MigrationRunner import MigrationRunner

MIGRATIONS_DIR = Path(__file__).parent / "Db" / "Migrations"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    pool = ConnectionPool(settings.database_url)
    await pool.connect()
    await MigrationRunner(pool, MIGRATIONS_DIR).run()
    app.state.pool = pool
    try:
        yield
    finally:
        await pool.close()


app = FastAPI(title="Books API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(v1_router)


@app.get("/health")
async def health() -> dict[str, str]:
    pool: ConnectionPool = app.state.pool
    async with pool.acquire() as conn:
        await conn.fetchval("SELECT 1")
    return {"status": "ok"}
