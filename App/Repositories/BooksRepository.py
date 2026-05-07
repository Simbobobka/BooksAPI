from asyncpg import Connection, Record

_SORT_MAP: dict[str, str] = {
    "title": "lower(b.title)",
    "year": "b.published_year",
    "created_at": "b.created_at",
    "author": """(
        SELECT MIN(COALESCE(a2.pen_name, a2.name))
        FROM book_authors ba2
        JOIN authors a2 ON a2.id = ba2.author_id
        WHERE ba2.book_id = b.id
    )""",
}


class BooksRepository:
    _INSERT = """
        WITH inserted AS (
            INSERT INTO books (title, published_year, genre_id)
            VALUES ($1, $2, $3)
            RETURNING id, title, published_year, genre_id, created_at, updated_at
        )
        SELECT i.id, i.title, i.published_year, i.created_at, i.updated_at,
               g.id AS genre_id, g.name AS genre_name
        FROM inserted i
        JOIN genres g ON g.id = i.genre_id
    """

    _SELECT_BY_ID = """
        SELECT b.id, b.title, b.published_year, b.created_at, b.updated_at,
               g.id AS genre_id, g.name AS genre_name
        FROM books b
        JOIN genres g ON g.id = b.genre_id
        WHERE b.id = $1
    """

    _DELETE = "DELETE FROM books WHERE id = $1 RETURNING id"

    _SET_AUTHORS_DELETE = "DELETE FROM book_authors WHERE book_id = $1"

    _SET_AUTHORS_INSERT = "INSERT INTO book_authors (book_id, author_id) VALUES ($1, $2)"

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    async def create(self, title: str, published_year: int, genre_id: int) -> Record:
        return await self._connection.fetchrow(self._INSERT, title, published_year, genre_id)

    async def get_by_id(self, book_id: int) -> Record | None:
        return await self._connection.fetchrow(self._SELECT_BY_ID, book_id)

    async def list(
        self,
        title: str | None,
        genre: str | None,
        author: str | None,
        year_from: int | None,
        year_to: int | None,
        sort_by: str,
        order: str,
        limit: int,
        offset: int,
    ) -> tuple[list[Record], int]:
        conditions: list[str] = []
        params: list = []

        def p(val) -> str:
            params.append(val)
            return f"${len(params)}"

        if title is not None:
            ref = p(f"%{title}%")
            conditions.append(f"lower(b.title) LIKE lower({ref})")

        if genre is not None:
            ref = p(genre)
            conditions.append(f"lower(g.name) = lower({ref})")

        if year_from is not None:
            ref = p(year_from)
            conditions.append(f"b.published_year >= {ref}")

        if year_to is not None:
            ref = p(year_to)
            conditions.append(f"b.published_year <= {ref}")

        if author is not None:
            ref = p(f"%{author}%")
            conditions.append(f"""EXISTS (
                SELECT 1 FROM book_authors ba2
                JOIN authors a2 ON a2.id = ba2.author_id
                WHERE ba2.book_id = b.id
                AND (lower(a2.name) LIKE lower({ref})
                     OR lower(COALESCE(a2.pen_name, '')) LIKE lower({ref}))
            )""")

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sort_expr = _SORT_MAP.get(sort_by, "b.created_at")
        order_dir = "ASC" if order == "asc" else "DESC"

        base = f"FROM books b JOIN genres g ON g.id = b.genre_id {where}"

        total: int = await self._connection.fetchval(f"SELECT COUNT(*) {base}", *params)

        limit_ref = p(limit)
        offset_ref = p(offset)

        rows = await self._connection.fetch(
            f"""SELECT b.id, b.title, b.published_year, b.created_at, b.updated_at,
                       g.id AS genre_id, g.name AS genre_name
                {base}
                ORDER BY {sort_expr} {order_dir}
                LIMIT {limit_ref} OFFSET {offset_ref}""",
            *params,
        )
        return list(rows), total

    async def update(
        self,
        book_id: int,
        title: str | None,
        published_year: int | None,
        genre_id: int | None,
    ) -> Record | None:
        sets: list[str] = []
        params: list = []

        def p(val) -> str:
            params.append(val)
            return f"${len(params)}"

        if title is not None:
            sets.append(f"title = {p(title)}")
        if published_year is not None:
            sets.append(f"published_year = {p(published_year)}")
        if genre_id is not None:
            sets.append(f"genre_id = {p(genre_id)}")

        if not sets:
            return await self.get_by_id(book_id)

        sets.append("updated_at = NOW()")
        book_ref = p(book_id)

        return await self._connection.fetchrow(
            f"""WITH updated AS (
                    UPDATE books SET {', '.join(sets)}
                    WHERE id = {book_ref}
                    RETURNING id, title, published_year, genre_id, created_at, updated_at
                )
                SELECT u.id, u.title, u.published_year, u.created_at, u.updated_at,
                       g.id AS genre_id, g.name AS genre_name
                FROM updated u JOIN genres g ON g.id = u.genre_id""",
            *params,
        )

    async def delete(self, book_id: int) -> bool:
        result = await self._connection.fetchval(self._DELETE, book_id)
        return result is not None

    async def set_authors(self, book_id: int, author_ids: list[int]) -> None:
        await self._connection.execute(self._SET_AUTHORS_DELETE, book_id)
        if author_ids:
            await self._connection.executemany(
                self._SET_AUTHORS_INSERT,
                [(book_id, aid) for aid in author_ids],
            )
