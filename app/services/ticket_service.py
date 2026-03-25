
from datetime import datetime
from sqlalchemy import update
from app.db.session import AsyncSessionLocal as async_session
from app.db.models.ticket import Ticket


from uuid import UUID as PyUUID

class TicketService:

    @staticmethod
    async def create_ticket(olt, onu_uuid, alert):
        async with async_session() as session:

            if onu_uuid:
                if not isinstance(onu_uuid, PyUUID):
                    onu_uuid = PyUUID(str(onu_uuid))
                    
                    
            device_id = str(alert.get("device_id"))

            alarm_id = str(
                alert.get("alarm_id") or f"{onu_uuid}-{alert.get('event')}"
            )

            ticket = Ticket(
                olt_id=olt.id,  # ✅ langsung
                onu_id=onu_uuid,  # ✅ sudah clean UUID
                device_id=device_id,
                alarm_id=alarm_id,
                event=alert.get("event"),
                message=alert.get("message"),
                status="OPEN"
            )

            session.add(ticket)

            await session.flush()
            await session.refresh(ticket)
            await session.commit()

            # menambahkan print untuk debuging
            print(f"🎫 Ticket CREATED: {ticket.id}")
            print("FINAL TYPE onu_id:", type(onu_uuid))
            print("TYPE onu_uuid FINAL:", type(onu_uuid))
            print("VALUE onu_uuid:", onu_uuid)
            return ticket.id
        
        
    @staticmethod
    async def acknowledge_ticket(alarm_id, user_name):
        if not alarm_id:
            print("❌ Invalid alarm_id")
            return

        async with async_session() as session:
            try:
                stmt = (
                    update(Ticket)
                    .where(Ticket.alarm_id == alarm_id)
                    .values(
                        status="ACK",
                        acknowledged_by=user_name,
                        acknowledged_at=datetime.utcnow()
                    )
                    .returning(Ticket.id)
                )

                result = await session.execute(stmt)
                updated = result.fetchone()

                await session.commit()

                if not updated:
                    print(f"⚠️ No ticket found for alarm_id={alarm_id}")
                else:
                    print(f"🎫 Ticket ACK: {alarm_id} by {user_name}")

            except Exception as e:
                print("❌ Ticket ACK error:", e)
                
                
    