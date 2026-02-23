## ========= models.py =============


from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .connection import Base


class ONUStatus(Base):
    __tablename__ = "onu_status"

    id = Column(Integer, primary_key=True, index=True)
    frame = Column(Integer)
    slot = Column(Integer)
    port = Column(Integer)
    onu_id = Column(Integer)
    status = Column(String)
    rx_power = Column(Float)
    tx_power = Column(Float)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
