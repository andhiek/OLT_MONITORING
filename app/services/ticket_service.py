
from datetime import datetime
from sqlalchemy import update
from app.db.session import AsyncSessionLocal as async_session
from app.db.models.ticket import Ticket


from uuid import UUID as PyUUID
STATUS_OPEN = "OPEN"
STATUS_ACK = "ACK"
STATUS_RESOLVED = "RESOLVED"
class TicketService:

    @staticmethod
    async def create_ticket(olt, onu_uuid, alert):
        async with async_session() as session:

            if onu_uuid:
                if not isinstance(onu_uuid, PyUUID):
                    onu_uuid = PyUUID(str(onu_uuid))

            device_id = str(alert.get("device_id"))

            # 🔥 WAJIB: alarm_id HARUS UNIK PER INCIDENT
            alarm_id = str(
                alert.get("alarm_id") or f"{onu_uuid}-{alert.get('event')}-{int(datetime.utcnow().timestamp())}"
            )

            from sqlalchemy import select

            # =============================
            # ✅ DUPLICATE CHECK (PER ALARM_ID)
            # =============================
            existing = await session.execute(
                select(Ticket).where(
                    Ticket.alarm_id == alarm_id
                )
            )
            existing_ticket = existing.scalar()

            if existing_ticket:
                print(f"⚠️ DUPLICATE BLOCKED (same alarm_id): {alarm_id}")
                return {
                    "ticket_id": existing_ticket.id,
                    "alarm_id": existing_ticket.alarm_id
                }

            # =============================
            # 🚀 CREATE NEW TICKET (SELALU BOLEH)
            # =============================
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
            
            from sqlalchemy import select , update
            
            # 🔍 1. ambil ticket dulu
            result = await session.execute(
                select(Ticket).where(Ticket.alarm_id == alarm_id)
            )
            ticket = result.scalar()
            
            # ❌ tidak ditemukan
            if not ticket:
                print(f"⚠️ No ticket found for alarm_id {alarm_id}")
                return {"status": "MOT FOUND"}
        
            
            # ⚠️ sudah resolved
            if str(ticket.status) == "RESOLVED":
                print(f"⚠️ Ticket {ticket.id} already RESOLVED")
                return {"status": "RESOLVED"}

            if str(ticket.status) == "ACK":
                print(f"⚠️ Ticket {ticket.id} already ACKNOWLEDGED")
                return {"status": "ALREADY_ACK"}
            
            print(type(ticket.status), ticket.status)
                
            # ✅ 2. update ke ACK
            await session.execute(
                update(Ticket)
                .where(Ticket.id == ticket.id)
                .values(
                    status = "ACK",
                    acknowledged_by = user_name if user_name else "SYSTEM",
                    acknowledged_at = datetime.utcnow()
                    
                )
            )
            
            
            await session.commit()
            
            print(f"🎫 Ticket ACK: {alarm_id} by {user_name}")
            
            return {
                "status": "SUCCESS",
                "ticket_id": ticket.id
            }
                
            
                
    
    
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
                        Ticket.event == "ONU_OFFLINE", # pastikan kta resolve berdasarkan event DOWN yang sesuai
                        Ticket.status.in_(["OPEN", "ACK"])
                    )
                    .order_by(Ticket.created_at.desc())
                    .limit(1)
                )

                ticket = result.scalar()

                if not ticket:
                    print(f"⚠️ No ACTIVE ticket for ONU {onu_uuid}")
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
                        
                        
                    )
                )
                

                await session.commit()

                print(f"✅ RESOLVED ticket {ticket.id}")

                ack = ticket.acknowledged_by

                if not str(ack) or str(ack).lower() == "none":
                    handled_by = "SYSTEM"
                else:
                    handled_by = str(ack)

                return {
                    "ticket_id": ticket.id,
                    "duration": duration_str,
                    "handled_by": handled_by
                }
                
                

            except Exception as e:
                print("❌ Resolve error:", e)
                return None
            
            
            