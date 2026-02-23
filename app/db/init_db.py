# =========== init_db.py ===========


import asyncio

from app.db.session import engine
from app.db.base import Base

# penting: import semua model supaya ter-register
from app.db import models  # noqa


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(init_db())
