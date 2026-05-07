from pathlib import Path

from App.Db.ConnectionPool import ConnectionPool


class MigrationRunner:
    _TRACKING_TABLE_DDL = """
        CREATE TABLE IF NOT EXISTS _migrations (
            name TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """

    def __init__(self, pool: ConnectionPool, migrations_dir: Path) -> None:
        self._pool = pool
        self._migrations_dir = migrations_dir

    async def run(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(self._TRACKING_TABLE_DDL)
            applied = {row["name"] for row in await conn.fetch("SELECT name FROM _migrations")}

            for file in sorted(self._migrations_dir.glob("*.sql")):
                if file.name in applied:
                    continue
                sql = file.read_text(encoding="utf-8")
                async with conn.transaction():
                    await conn.execute(sql)
                    await conn.execute(
                        "INSERT INTO _migrations (name) VALUES ($1)",
                        file.name,
                    )
