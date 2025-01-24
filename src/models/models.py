from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from .database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer)
    event_type = Column(String)
    description = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow) 