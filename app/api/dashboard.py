from fastapi import APIRouter
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models.ticket import Ticket
from app.services.state_cache import STATE

router = APIRouter()


# ===============================
# 🎫 TICKETS
# ===============================
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


# ===============================
# 📊 DASHBOARD SUMMARY
# ===============================
@router.get("/dashboard")
async def get_dashboard():

    total_onu = 0
    total_online = 0
    total_offline = 0
    total_active_alarms = 0

    olt_list = []

    for olt_id, data in STATE.get("olts", {}).items():

        onu_list = data.get("onu_list", [])
        alerts = data.get("alerts", [])

        onu_total = len(onu_list)
        onu_online = sum(1 for o in onu_list if o.get("status") == "ONLINE")
        onu_offline = sum(1 for o in onu_list if o.get("status") == "OFFLINE")

        active_alarms = sum(1 for a in alerts if a.get("status") == "DOWN")

        total_onu += onu_total
        total_online += onu_online
        total_offline += onu_offline
        total_active_alarms += active_alarms

        # 🔥 Health logic (lebih realistis)
        if onu_offline == 0:
            health = "OK"
        elif onu_offline < onu_total * 0.5:
            health = "DEGRADED"
        else:
            health = "CRITICAL"

        olt_list.append({
            "olt_id": str(olt_id),
            "olt_name": data.get("olt_name", str(olt_id)),
            "onu_total": onu_total,
            "onu_online": onu_online,
            "onu_offline": onu_offline,
            "active_alarms": active_alarms,
            "health": health
        })

    return {
        "onu_total": total_onu,
        "onu_online": total_online,
        "onu_offline": total_offline,
        "active_alarms": total_active_alarms,
        "olt_count": len(STATE.get("olts", {})),
        "last_update": str(STATE.get("last_update")),
        "olts": olt_list
    }


# ===============================
# 🧩 OLT DETAIL
# ===============================
@router.get("/olts")
async def get_olts():

    result = []

    for olt_id, data in STATE.get("olts", {}).items():
        
        
        
        onu_list = data.get("onu_list", [])
        alerts = data.get("alerts", [])

        online = sum(1 for o in onu_list if o.get("status") == "ONLINE")
        offline = sum(1 for o in onu_list if o.get("status") == "OFFLINE")

        result.append({
            "olt_id": str(olt_id),
            "olt_name": data.get("olt_name", str(olt_id)),
            "onu_total": len(onu_list),
            "online": online,
            "offline": offline,
            "active_alarms": sum(1 for a in alerts if a.get("status") == "DOWN"),
        })

    return result


# ===============================
# 🔥 INCIDENTS (CORE FEATURE)
# ===============================
@router.get("/incidents")
async def get_incidents():

    incidents = STATE.get("incidents", [])

    result = []

    for inc in incidents:

        root = inc.get("root_alert", {})

        result.append({
            "olt": inc.get("olt_name"),
            "root_device": root.get("device_id"),
            "event": root.get("event"),
            "impact": inc.get("impact_count"),
            "status": "OPEN" if inc.get("is_active") else "RESOLVED",
            "time": str(inc.get("created_at"))
        })

    return result

