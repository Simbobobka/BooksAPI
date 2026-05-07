from asyncpg import Connection, Record


class AuthorsRepository:
    _SELECT = """
        SELECT id, name, last_name, middle_name, pen_name, created_at, updated_at
        FROM authors
        WHERE name = $1
          AND COALESCE(last_name, '')   = COALESCE($2, '')
          AND COALESCE(middle_name, '') = COALESCE($3, '')
          AND COALESCE(pen_name, '')    = COALESCE($4, '')
    """

    _INSERT = """
        INSERT INTO authors (name, last_name, middle_name, pen_name)
        VALUES ($1, $2, $3, $4)
        RETURNING id, name, last_name, middle_name, pen_name, created_at, updated_at
    """

    _SELECT_BY_BOOK_IDS = """
        SELECT ba.book_id, a.id, a.name, a.last_name, a.middle_name, a.pen_name
        FROM book_authors ba
        JOIN authors a ON a.id = ba.author_id
        WHERE ba.book_id = ANY($1::bigint[])
        ORDER BY a.last_name NULLS LAST, a.name
    """

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    async def get_or_create(
        self,
        name: str,
        last_name: str | None,
        middle_name: str | None,
        pen_name: str | None,
    ) -> Record:
        record = await self._connection.fetchrow(
            self._SELECT, name, last_name, middle_name, pen_name
        )
        if record is not None:
            return record
        return await self._connection.fetchrow(self._INSERT, name, last_name, middle_name, pen_name)

    async def get_by_book_ids(self, book_ids: list[int]) -> list[Record]:
        return await self._connection.fetch(self._SELECT_BY_BOOK_IDS, book_ids)
