

## ============= main.py ===========

import asyncio

from app.database.models import Base
from app.database.connection import engine
from app.services.topology_service import load_topology
from app.telegram.bot import start_bot




async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        print("Loading network topology...")

        await load_topology()
        print("Topology loaded")

async def main():
    await init_db()
    await start_bot()


if __name__ == "__main__":
    asyncio.run(main())

