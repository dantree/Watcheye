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

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str

class RegisterResponse(BaseModel):
    message: str
    username: str

class TokenData(BaseModel):
    username: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"