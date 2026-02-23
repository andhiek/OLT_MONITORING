# =========== olt_services.py ===========

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import AsyncSessionLocal
from app.db.models.olt import OLT


async def get_active_olts():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(OLT)
            .options(selectinload(OLT.client))  # <-- penting
            .where(OLT.is_active == True)
        )
        return result.scalars().all()
