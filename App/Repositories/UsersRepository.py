from asyncpg import Connection, Record


class UsersRepository:
    _INSERT = """
        INSERT INTO users (email, password_hash)
        VALUES ($1, $2)
        RETURNING id, email, created_at
    """

    _SELECT_BY_EMAIL = """
        SELECT id, email, password_hash, created_at
        FROM users
        WHERE email = $1
    """

    _SELECT_BY_ID = """
        SELECT id, email, created_at
        FROM users
        WHERE id = $1
    """

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    async def create(self, email: str, password_hash: str) -> Record:
        return await self._connection.fetchrow(self._INSERT, email, password_hash)

    async def get_by_email(self, email: str) -> Record | None:
        return await self._connection.fetchrow(self._SELECT_BY_EMAIL, email)

    async def get_by_id(self, user_id: int) -> Record | None:
        return await self._connection.fetchrow(self._SELECT_BY_ID, user_id)
