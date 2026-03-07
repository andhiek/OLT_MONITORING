## ========= connection.py ==========


import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker,declarative_base

DATABASE_URL = "postgresql+asyncpg://noc_user:capung21@localhost:5432/noc_saas"

engine = create_async_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(
    Bind = engine,
    class_=AsyncSession,
    expire_on_commit=False
)
Base = declarative_base()



async def test_connection():
    try:
        conn = await engine.connect()
        print("✅ Database connected successfully!")
        await conn.close()
    except Exception as e:
        print("❌ Connection failed:", e)

if __name__ == "__main__":
    asyncio.run(test_connection())