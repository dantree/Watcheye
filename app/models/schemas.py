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

# # 로그인 요청 스키마
# class UserLogin(BaseModel):
#     username: str
#     password: str

# # 로그인 응답 스키마
# class Token(BaseModel):
#     access_token: str
#     token_type: str = "bearer"
    
# # 토큰 데이터 스키마
# class TokenData(BaseModel):
#     username: Optional[str] = None

# # 사용자 생성 스키마
# class UserCreate(BaseModel):
#     username: str
#     password: str

# # 사용자 정보 스키마
# class User(BaseModel):
#     id: int
#     username: str
#     is_active: bool
#     created_at: datetime

#     class Config:
#         orm_mode = True