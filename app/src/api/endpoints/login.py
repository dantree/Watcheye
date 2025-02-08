# api/endpoints/login.py
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...models.database import get_db
from ...models.models import User
from ...models.schemas import UserLogin, UserResponse, LoginResponse
from ...services.auth import create_access_token, get_current_user

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
async def login(
    response: Response,            # 기본값이 없는 인자를 먼저 선언
    user_data: UserLogin,          # 요청 본문에서 받을 데이터
    db: Session = Depends(get_db)  # 기본값(Depends 사용)을 가진 인자는 마지막에 선언
):
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not user.verify_password(user_data.password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.username})
    # 토큰을 HttpOnly 쿠키에 저장합니다.
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age= 60 * 60  # 만료 시간(초 단위)
    )
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

@router.post("/auth/logout")
async def logout(response: Response):
    # 클라이언트에 설정된 access_token 쿠키를 삭제합니다.
    response.delete_cookie("access_token")
    return {"message": "Successfully logged out"}