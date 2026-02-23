import asyncio
from sqlalchemy import select
from datetime import datetime
from uuid import UUID


from app.db.session import AsyncSessionLocal
from app.db.models import User
from app.db.models import Alarm


async def test_ack():
    alarm_id = UUID("dc78bd46-d13e-4c06-be28-2efdfa10dbd5")
    telegram_id = 197455065

    async with AsyncSessionLocal() as session:

        user = await session.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )

        if not user:
            print("User not found")
            return

        alarm = await session.get(Alarm, alarm_id)

        if not alarm:
            print("Alarm not found")
            return

        alarm.acknowledged_by = user.id
        alarm.acknowledged_name = user.username
        alarm.acknowledged_at = datetime.utcnow()

        await session.commit()

        print("ACK SUCCESS")


if __name__ == "__main__":
    asyncio.run(test_ack())