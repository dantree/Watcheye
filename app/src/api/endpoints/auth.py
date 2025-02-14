from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from ...models.database import get_db
from ...models.models import User
from ...models.schemas import Token, TokenData, UserLogin, UserCreate, RegisterResponse, LoginResponse
from pydantic import BaseModel
from fastapi.responses import RedirectResponse, JSONResponse

# JWT 설정
SECRET_KEY = "your-secret-key-keep-it-secret"  # 실제 운영 환경에서는 환경 변수로 관리해야 합니다
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if token:
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
    if token is None:
        token = await oauth2_scheme(request)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증에 실패했습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

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
            "email": user.email
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="회원가입에 실패했습니다")

@router.post("/auth/login")
async def login(
    response: Response,
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not user.verify_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    # 토큰을 HttpOnly 쿠키에 저장
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,  # 30분
        path="/",
        samesite="lax"
    )
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "email": user.email
    }

@router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    return {"message": "로그아웃되었습니다"}

# 추가: 현재 사용자 정보 반환 엔드포인트
class UserResponse(BaseModel):
    email: str
    name: str
    phone: str

@router.get("/me", response_model=UserResponse)
async def read_me(current_user = Depends(get_current_user)):
    return UserResponse(
        email=current_user.email,
        name=current_user.name,
        phone=current_user.phone
    ) 