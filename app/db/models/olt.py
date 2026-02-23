### =========== olt.py =========


import uuid
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OLT(Base):
    __tablename__ = "olts"

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

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    host: Mapped[str] = mapped_column(String(100), nullable=False)

    community: Mapped[str] = mapped_column(String(100), nullable=False)

    brand: Mapped[str] = mapped_column(String(50), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    client = relationship("Client")
    onus = relationship("ONU", back_populates="olt")
