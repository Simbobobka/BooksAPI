from asyncpg import Connection, Record


class AuthorsRepository:
    _SELECT = """
        SELECT id, name, pen_name, created_at, updated_at
        FROM authors
        WHERE name = $1 AND COALESCE(pen_name, '') = COALESCE($2, '')
    """

    _INSERT = """
        INSERT INTO authors (name, pen_name)
        VALUES ($1, $2)
        RETURNING id, name, pen_name, created_at, updated_at
    """

    _SELECT_BY_BOOK_IDS = """
        SELECT ba.book_id, a.id, a.name, a.pen_name
        FROM book_authors ba
        JOIN authors a ON a.id = ba.author_id
        WHERE ba.book_id = ANY($1::bigint[])
        ORDER BY a.name
    """

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    async def get_or_create(self, name: str, pen_name: str | None) -> Record:
        record = await self._connection.fetchrow(self._SELECT, name, pen_name)
        if record is not None:
            return record
        return await self._connection.fetchrow(self._INSERT, name, pen_name)

    async def get_by_book_ids(self, book_ids: list[int]) -> list[Record]:
        return await self._connection.fetch(self._SELECT_BY_BOOK_IDS, book_ids)
