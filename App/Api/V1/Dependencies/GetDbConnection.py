from collections.abc import AsyncIterator
from typing import Annotated

import asyncpg
from fastapi import Depends, Request


async def get_db_connection(request: Request) -> AsyncIterator[asyncpg.Connection]:
    pool = request.app.state.pool
    async with pool.acquire() as connection:
        yield connection


DbConnection = Annotated[asyncpg.Connection, Depends(get_db_connection)]
