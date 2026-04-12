
from fastapi import APIRouter
from sqlalchemy import func
from typing import List
from app.db.session import AsyncSessionLocal
from app.db.models.ticket import Ticket
from sqlalchemy import select
from app.services.state_cache import STATE

router = APIRouter()




@router.get("/tickets")
async def get_tickets():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Ticket).order_by(Ticket.created_at.desc())
        )
        tickets = result.scalars().all()

        return [
            {
                "id": str(t.id),
                "onu_id": str(t.onu_id),
                "event": t.event,
                "status": t.status,
                "ack_by": t.acknowledged_by,
                "created_at": str(t.created_at),
            }
            for t in tickets
        ]



@router.get("/dashboard")
async def get_dashboard():

    total_onu = 0
    online = 0
    offline = 0
    total_alarms = 0

    olt_list = []   # 🔥 TAMBAHAN

    for olt_id, data in STATE["olts"].items():

        olt_name = data.get("olt_name", str(olt_id))
        onu_list = data.get("onu_list", [])
        alerts = data.get("alerts", [])

        onu_total = len(onu_list)
        onu_online = sum(1 for o in onu_list if o.get("status") == "ONLINE")
        onu_offline = sum(1 for o in onu_list if o.get("status") == "OFFLINE")

        total_onu += onu_total
        online += onu_online
        offline += onu_offline
        total_alarms += len(alerts)

        # 🔥 Tambahin ini
        olt_list.append({
            "olt_id": str(olt_id),
            "olt_name": olt_name,
            "onu_total": onu_total,
            "onu_online": onu_online,
            "active_alarms": len(alerts),
            "health": "OK" if onu_offline == 0 else "DEGRADED"
        })

    return {
        "onu_total": total_onu,
        "onu_online": online,
        "onu_offline": offline,
        "active_alarms": total_alarms,
        "olt_count": len(STATE["olts"]),
        "last_update": str(STATE["last_update"]),
        "olts": olt_list   # 🔥 WAJIB ADA
    }
    
@router.get("/olts")
async def get_olts():
        result = []

        for olt_id, data in STATE["olts"].items():
            onu_list = data.get("onu_list", [])
            alerts = data.get("alerts", [])

            online = sum(1 for o in onu_list if o.get("status") == "ONLINE")
            offline = sum(1 for o in onu_list if o.get("status") == "OFFLINE")

            result.append({
                "olt_id": str(olt_id),
                "onu_total": len(onu_list),
                "online": online,
                "offline": offline,
                "alerts": len(alerts),
            })

        return result