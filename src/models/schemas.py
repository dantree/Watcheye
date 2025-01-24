from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EventBase(BaseModel):
    camera_id: int
    event_type: str
    description: Optional[str] = None

class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: int
    timestamp: datetime
    
    class Config:
        orm_mode = True 