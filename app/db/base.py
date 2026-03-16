## ======= base.py ==========

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass


# IMPORTANT: import semua model
from app.db.models.client import Client
from app.db.models.olt import OLT
from app.db.models.onu import ONU
from app.db.models.splitter import Splitter