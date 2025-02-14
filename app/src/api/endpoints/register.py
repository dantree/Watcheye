from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...models.database import get_db
from ...models.models import User
from ...models.schemas import UserCreate, RegisterResponse

router = APIRouter()

@router.post("/auth/register", response_model=RegisterResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
    
    user = User(
        email=user_data.email,
        phone=user_data.phone,
        name=user_data.name,
        hashed_password=User.get_password_hash(user_data.password)
    )
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return {
            "message": "회원가입이 완료되었습니다",
            "username": user.email
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="회원가입에 실패했습니다")