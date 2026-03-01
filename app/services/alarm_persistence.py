from datetime import datetime
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models.alarm import Alarm


# ==========================================================
# CREATE ALARM
# ==========================================================
async def create_alarm(olt, onu_id, alarm_type, message):
    async with AsyncSessionLocal() as session:
        try:
            # Cek apakah sudah ada alarm aktif dengan tipe sama
            result = await session.execute(
                select(Alarm).where(
                    Alarm.olt_id == olt.id,
                    Alarm.onu_id == onu_id,
                    Alarm.type == alarm_type,
                    Alarm.is_resolved.is_(False)
                )
            )

            existing = result.scalar_one_or_none()

            if existing:
                return None  # Alarm sudah ada

            alarm = Alarm(
                client_id=olt.client_id,
                olt_id=olt.id,
                onu_id=onu_id,
                type=alarm_type,
                message=message,
                is_resolved=False,
                created_at=datetime.utcnow()
            )

            session.add(alarm)
            await session.commit()
            await session.refresh(alarm)

            return alarm.id  # penting untuk Telegram ACK button

        except Exception:
            await session.rollback()
            raise


# ==========================================================
# RESOLVE ALARM
# ==========================================================
async def resolve_alarm(olt, onu_id, alarm_type):
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Alarm).where(
                    Alarm.olt_id == olt.id,
                    Alarm.onu_id == onu_id,
                    Alarm.type == alarm_type,
                    Alarm.is_resolved.is_(False)
                )
            )

            alarm = result.scalar_one_or_none()

            if not alarm:
                return None

            alarm.is_resolved = True
            alarm.resolved_at = datetime.utcnow()

            await session.commit()
            await session.refresh(alarm)

            # hitung durasi
            duration = alarm.resolved_at - alarm.created_at

            return {
                "duration": str(duration).split(".")[0],
                "acknowledged_by": alarm.acknowledged_at
            }

        except Exception:
            await session.rollback()
            raise
# ==========================================================
# ACKNOWLEDGE ALARM
# ==========================================================
async def acknowledge_alarm(alarm_id, user):
    async with AsyncSessionLocal() as session:
        try:
            alarm = await session.get(Alarm, alarm_id)

            if not alarm:
                return False
            
            
            if alarm.is_resolved:
                return {"status": "ALREADY_RESOLVED"}

            if alarm.acknowledged_at:
                return False 

        
            
            alarm.acknowledged_at = datetime.utcnow()

            await session.commit()

            return True
        
        except Exception:
            await session.rollback()
            raise


# ==========================================================
# GET ACTIVE ALARM (OPTIONAL HELPER)
# ==========================================================
async def get_active_alarm_by_id(alarm_id):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Alarm).where(
                Alarm.id == alarm_id,
                Alarm.is_resolved.is_(False)
            )
        )
        return result.scalar_one_or_none()