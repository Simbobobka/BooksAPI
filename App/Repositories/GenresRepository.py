from asyncpg import Connection, Record


class GenresRepository:
    _SELECT_BY_NAME = """
        SELECT id, name
        FROM genres
        WHERE lower(name) = lower($1)
    """

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    async def get_by_name(self, name: str) -> Record | None:
        return await self._connection.fetchrow(self._SELECT_BY_NAME, name)
