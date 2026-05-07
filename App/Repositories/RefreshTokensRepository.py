from asyncpg import Connection, Record


class RefreshTokensRepository:
    _INSERT = """
        INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
        VALUES ($1, $2, NOW() + ($3 || ' days')::interval)
    """

    _SELECT_BY_HASH = """
        SELECT id, user_id, token_hash, expires_at
        FROM refresh_tokens
        WHERE token_hash = $1 AND expires_at > NOW()
    """

    _DELETE = "DELETE FROM refresh_tokens WHERE token_hash = $1"

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    async def create(self, user_id: int, token_hash: str, expire_days: int) -> None:
        await self._connection.execute(self._INSERT, user_id, token_hash, str(expire_days))

    async def get_by_hash(self, token_hash: str) -> Record | None:
        return await self._connection.fetchrow(self._SELECT_BY_HASH, token_hash)

    async def delete(self, token_hash: str) -> None:
        await self._connection.execute(self._DELETE, token_hash)
