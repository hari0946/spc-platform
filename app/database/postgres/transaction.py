"""Transaction boundary helper.

Repositories that need to perform several related writes atomically (e.g.
baseline approval: supersede the old ACTIVE baseline + activate the new
one) accept an optional `connection` parameter. When none is supplied they
acquire one from the pool for a single statement; when a caller wants
several repository calls to share one transaction, it uses this context
manager and passes the resulting connection through explicitly.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg

from app.database.postgres.connection import get_pool


@asynccontextmanager
async def transaction() -> AsyncIterator[asyncpg.Connection]:
    pool = get_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            yield connection
