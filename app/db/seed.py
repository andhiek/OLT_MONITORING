# =========== seed.py =============

import asyncio
from app.db.session import AsyncSessionLocal
from app.db.models.client import Client
from app.db.models.olt import OLT


async def seed():
    async with AsyncSessionLocal() as session:

        client = Client(
            name="Demo ISP",
            package_type="basic",
            telegram_chat_id="197455065"
        )

        session.add(client)
        await session.flush()  # supaya dapat client.id

        olt = OLT(
            client_id=client.id,
            name="OLT-1",
            host="192.168.1.1",
            community="public",
            brand="ZTE"
        )

        session.add(olt)

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
