from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...models.database import get_db
from ...models.models import User
from ...models.schemas import UserCreate, RegisterResponse

router = APIRouter()

@router.post("/auth/register", response_model=RegisterResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")

    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if user_data.mobile_phone:
        if db.query(User).filter(User.mobile_phone == user_data.mobile_phone).first():
            raise HTTPException(status_code=400, detail="Mobile phone already registered")
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        mobile_phone=user_data.mobile_phone,
        password_hash=User.get_password_hash(user_data.password)
    )
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return {
            "message": "User created successfully",
            "username": user.username,
            "email": user.email
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Registration failed")