import asyncpg


class ConnectionPool:
    def __init__(self, database_url: str, min_size: int = 1, max_size: int = 10) -> None:
        self._database_url = database_url
        self._min_size = min_size
        self._max_size = max_size
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(
            self._database_url,
            min_size=self._min_size,
            max_size=self._max_size,
        )

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    def acquire(self):
        if self._pool is None:
            raise RuntimeError("Connection pool is not initialized")
        return self._pool.acquire()
