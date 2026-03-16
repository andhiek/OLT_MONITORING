# ========== splitter.py ===========


import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Splitter(Base):
    __tablename__ = "splitters"

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
    
    
    # RELATIONSHIP KE OLT

    pon_port: Mapped[str] = mapped_column(String(50), nullable=False)

    name: Mapped[str] = mapped_column(String(50), nullable=False)

    olt = relationship("OLT", back_populates="splitters")
    onus = relationship("ONU", back_populates="splitter")
    
    