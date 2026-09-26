import asyncio
from sqlalchemy import text
from backend.database.db_store import engine

async def main():
    async with engine.connect() as conn:
        for table in [
            "users",
            "projects",
            "content_ideas",
            "outlines",
            "drafts",
            "images",
            "ai_generations",
        ]:
            res = await conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}';"))
            cols = [r[0] for r in res.fetchall()]
            print(f"Table '{table}': {cols}")

if __name__ == "__main__":
    asyncio.run(main())
