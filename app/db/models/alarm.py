# ========== alarm.py ===========

import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer


from app.db.base import Base


class Alarm(Base):
    __tablename__ = "alarms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id"),
        nullable=False
    )

    olt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("olts.id"),
        nullable=False
    )

    onu_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("onus.id"),
        nullable=True
    )

    type: Mapped[str] = mapped_column(String(50), nullable=False)

    message: Mapped[str] = mapped_column(String(255), nullable=False)

    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    resolved_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )

    # ==============================
    # ACKNOWLEDGMENT FIELDS
    # ==============================

    acknowledged_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )

    acknowledged_name: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )

    acknowledged_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    

    # ==============================
    # SEVERITY & ESCALATION
    # ==============================

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium"
    )

    escalation_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )