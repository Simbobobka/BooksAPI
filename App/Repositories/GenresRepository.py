from asyncpg import Connection, Record


class GenresRepository:
    _SELECT_ALL = "SELECT id, name FROM genres ORDER BY name"

    _SELECT_BY_ID = "SELECT id, name FROM genres WHERE id = $1"

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    async def get_all(self) -> list[Record]:
        return await self._connection.fetch(self._SELECT_ALL)

    async def get_by_id(self, genre_id: int) -> Record | None:
        return await self._connection.fetchrow(self._SELECT_BY_ID, genre_id)
