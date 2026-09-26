"""Create the development database schema for Docker Compose startup."""

import asyncio

from sqlalchemy import text

from backend.database.db_schema import Base
from backend.database.db_store import engine


async def bootstrap_database() -> None:
    async with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            await connection.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(bootstrap_database())
