from fastapi import FastAPI, Depends
from loguru import logger
from .api.endpoints import events, cameras, views, system, auth, safety, login, register, settings, ws
from .models.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

# 현재 파일의 디렉토리를 기준으로 정적 파일 디렉토리 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
CAPTURES_DIR = BASE_DIR / "captures"

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # CSS와 관련된 보안 정책 수정
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://fonts.googleapis.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob:;"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app = FastAPI(title="지켜봄 서비스")

# 보안 미들웨어 추가
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 도메인을 지정해야 합니다
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 디렉토리 생성
os.makedirs(STATIC_DIR / "css", exist_ok=True)
os.makedirs(STATIC_DIR / "js", exist_ok=True)
os.makedirs(STATIC_DIR / "images", exist_ok=True)
os.makedirs(CAPTURES_DIR, exist_ok=True)

# 정적 파일 서빙 설정 수정
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/captures", StaticFiles(directory=str(CAPTURES_DIR)), name="captures")

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(views.router)

app.include_router(
    auth.router,
    prefix="/api",
    tags=["auth"]
)

app.include_router(
    cameras.router,
    prefix="/api/v1",
    tags=["cameras"]
)

app.include_router(
    events.router,
    prefix="/api/v1",
    tags=["events"]
)

app.include_router(
    system.router,
    prefix="/api/v1",
    tags=["system"]
)

app.include_router(
    safety.router,
    prefix="/api/v1",
    tags=["safety"]
)

app.include_router(
    login.router,
    prefix="/api/v1",
    tags=["login"]
)

app.include_router(
    register.router,
    prefix="/api/v1",
    tags=["register"]
)

app.include_router(
    settings.router,
    prefix="/api/v1",
    tags=["settings"]
)

app.include_router(
    ws.router,
    prefix="/api/v1",
    tags=["websocket"]
)

# 리다이렉션을 위한 라우트 추가
@app.get("/cameras")
async def redirect_cameras():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/v1/cameras")

@app.get("/")
async def root():
    return {"message": "지켜봄 서비스 API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting 지켜봄 서비스...")
    # 로그 저장 폴더 생성 (존재하지 않으면 생성)
    os.makedirs("logs", exist_ok=True)
    # Loguru 설정: logs/system.log 파일에 로그를 기록하며, 500MB마다 롤링 처리
    logger.add("logs/system.log", rotation="500 MB")
    # host를 '0.0.0.0'으로 설정하여 외부 접속 허용
    uvicorn.run(app, host="0.0.0.0", port=8001, access_log=True) 