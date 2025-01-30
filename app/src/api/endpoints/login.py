# api/endpoints/login.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...models.database import get_db
from ...models.models import User
from ...models.schemas import UserLogin, UserResponse, LoginResponse
from ...services.auth import create_access_token, get_current_user

router = APIRouter()

@router.post("/auth/login", response_model=LoginResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not user.verify_password(user_data.password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.username})
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        username=user.username
    )

@router.get("/auth/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "is_active": current_user.is_active
    }