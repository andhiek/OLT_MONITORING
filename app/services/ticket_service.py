
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

            from sqlalchemy import select

            # 🔥 1. CEK DUPLIKAT DULU
            existing = await session.execute(
                select(Ticket).where(
                    Ticket.onu_id == onu_uuid,
                    Ticket.event == alert.get("event"),
                    Ticket.status.in_(["OPEN", "ACK"])
                )
            )
            existing_ticket = existing.scalar()

            if existing_ticket:
                print(f"⚠️ DUPLICATE BLOCKED: {existing_ticket.alarm_id}")
                return {
                    "ticket_id": existing_ticket.id,
                    "alarm_id": existing_ticket.alarm_id
                }

            # 🔥 2. BARU CREATE
            print(f"🎯 Creating ticket: {alarm_id}")

            ticket = Ticket(
                olt_id=olt.id,
                onu_id=onu_uuid,
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

            # 🔥 3. WAJIB RETURN
            return {
                "ticket_id": ticket.id,
                "alarm_id": alarm_id
            }
            
        
        
    @staticmethod
    async def acknowledge_ticket(alarm_id, user_name):
        alarm_id = str(alarm_id).strip() # 🔥 SAFETY CONVERSION
        
        
        if not alarm_id:
                    print("❌ Invalid alarm_id")
                    return "NOT FOUND"
                
                
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
                    return False
                else:
                    print(f"🎫 Ticket ACK: {alarm_id} by {user_name}")
                    
                    return updated[0]

            except Exception as e:
                print("❌ Ticket ACK error:", e)
                
                
    
    
    # =============================
    # CORRELATION LOGIC resolve
    # =============================
    @staticmethod
    async def resolve_ticket(onu_uuid,event):
        async with async_session() as session:
            if onu_uuid and not isinstance(onu_uuid, PyUUID):
                onu_uuid = PyUUID(str(onu_uuid))
            try:
                from sqlalchemy import select, update

                # 🔥 cari ticket aktif
                result = await session.execute(
                    select(Ticket)
                    .where(
                        Ticket.onu_id == onu_uuid,
                        Ticket.event == "ONU_OFFLINE",
                        Ticket.status.in_(["OPEN", "ACK"])
                    )
                    .order_by(Ticket.created_at.desc())
                    .limit(1)
                )

                ticket = result.scalar()

                if not ticket:
                    print(f"⚠️ No active ticket for ONU {onu_uuid}")
                    return None
                
                

                now = datetime.utcnow()
                
                duration_sec = int((now - ticket.created_at).total_seconds())
                
                # 🔥 FORMAT BARU (HUMAN FRIENDLY)
                days = duration_sec // 86400
                hours = (duration_sec % 86400) // 3600
                minutes = (duration_sec % 3600) // 60

                parts = []

                if days:
                    parts.append(f"{days}d")
                if hours:
                    parts.append(f"{hours}h")
                if minutes:
                    parts.append(f"{minutes}m")

                duration_str = " ".join(parts) if parts else "0m"
                

                # 🔥 UPDATE pakai query (ANTI ERROR)
                await session.execute(
                    update(Ticket)
                    .where(Ticket.id == ticket.id)
                    .values(
                        status="RESOLVED",
                        resolved_at=now,
                        duration=duration_sec, # 🔥 SIMPAN KE DB
                        acknowledged_by=ticket.acknowledged_by or "SYSTEM AUTO RESOLVE "
                        
                    )
                )
                

                await session.commit()

                print(f"✅ RESOLVED ticket {ticket.id}")

                return {
                    "ticket_id": ticket.id,
                    "duration": duration_str,
                    "acknowledged_by": ticket.acknowledged_by
                }
                
                

            except Exception as e:
                print("❌ Resolve error:", e)
                return None
            
            
            