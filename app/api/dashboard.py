from fastapi import APIRouter
from sqlalchemy import func

from app.db.session import AsyncSessionLocal
from app.db.models.ticket import Ticket
from sqlalchemy import select

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
    async with AsyncSessionLocal() as session:

        total = await session.scalar(select(func.count(Ticket.id))) or 0

        open_tickets = await session.scalar(
            select(func.count()).where(Ticket.status == "OPEN")
        ) or 0

        closed_tickets = await session.scalar(
            select(func.count()).where(Ticket.status == "CLOSED")
        ) or 0

        health = "UNKNOWN"

        if open_tickets is not None:
            health = "GOOD" if open_tickets < 10 else "WARNING"

        return {
            "total_tickets": total,
            "open_tickets": open_tickets,
            "closed_tickets": closed_tickets,
            "health": health
        }