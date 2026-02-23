# =========== onu.py ===========



import uuid
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.base import Base


class ONU(Base):
    __tablename__ = "onus"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    olt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("olts.id"),
        nullable=False
    )

    onu_index: Mapped[str] = mapped_column(String(50), nullable=False)

    serial_number: Mapped[str] = mapped_column(String(100), nullable=True)

    last_status: Mapped[str] = mapped_column(String(20), nullable=True)

    last_power: Mapped[float] = mapped_column(Float, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    olt = relationship("OLT", back_populates="onus")
