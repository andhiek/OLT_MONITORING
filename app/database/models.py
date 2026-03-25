## ========= models.py =============


from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.db.base import Base
from app.db.session import engine


class ONUStatus(Base):
    __tablename__ = "onu_status"
    

    id = Column(Integer, primary_key=True, index=True)
    frame = Column(Integer)
    slot = Column(Integer)
    port = Column(Integer)
    onu_id = Column(Integer)
    device_id = Column(String,nullable=False)
    status = Column(String)
    rx_power = Column(Float)
    tx_power = Column(Float)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
