
# ========== app/db/models/ ticket.py ===========

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey,Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from app.db.base import Base



class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    olt_id = Column(UUID(as_uuid=True), ForeignKey("olts.id"))

    # 🔥 FIX DI SINI
    onu_id = Column(UUID(as_uuid=True), nullable=True) # HAPUS ForeignKey karena kita tidak punya tabel onus lagi
    alarm_id = Column(String, index=True)
    device_id = Column(String, nullable=False)

    event = Column(String)
    message = Column(String)

    status = Column(String, default="OPEN")

    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    
    
    