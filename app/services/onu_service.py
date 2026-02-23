# ============ onu_services.py =============



from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models.onu import ONU
from app.db.models.status_log import StatusLog


async def save_onu_data(olt, onu_list):

    onu_mapping = {}  # 👈 mapping index → uuid

    async with AsyncSessionLocal() as session:

        for onu_data in onu_list:

            result = await session.execute(
                select(ONU).where(
                    ONU.olt_id == olt.id,
                    ONU.onu_index == str(onu_data["id"])
                )
            )

            onu = result.scalar_one_or_none()

            if not onu:
                onu = ONU(
                    olt_id=olt.id,
                    onu_index=str(onu_data["id"]),
                    last_status=onu_data["status"],
                    last_power=onu_data["power"],
                )
                session.add(onu)
                await session.flush()  # supaya dapat UUID
            else:
                onu.last_status = onu_data["status"]
                onu.last_power = onu_data["power"]

            # simpan history
            log = StatusLog(
                olt_id=olt.id,
                onu_id=onu.id,
                status=onu_data["status"],
                power=onu_data["power"],
            )
            session.add(log)

            # 👇 simpan ke mapping
            onu_mapping[str(onu_data["id"])] = str(onu.id)

        await session.commit()

    return onu_mapping  # 👈 penting
