from fastapi import FastAPI
from loguru import logger
from .api.endpoints import events, cameras, views, system #,users
from .models.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware

# from app.api import users, events, cameras, views, system
# from app.models import engine, Base
# from fastapi.middleware.cors import CORSMiddleware
# from app.config import settings

app = FastAPI(title="지켜봄 서비스")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 origin을 지정해야 합니다
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(events.router, prefix="/api/v1")
app.include_router(cameras.router, prefix="/api/v1")
app.include_router(views.router, prefix="/view", tags=["views"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
# app.include_router(users.router, prefix="/api/v1/users")  # 사용자 라우터 추가
# 라우터 등록
# app.include_router(users.users_router, prefix="/api/v1/users")
# app.include_router(events.events_router, prefix="/api/v1/events")
# app.include_router(cameras.cameras_router, prefix="/api/v1/cameras")
# app.include_router(views.views_router, prefix="/view", tags=["views"])
# app.include_router(system.system_router, prefix="/api/v1/system", tags=["system"])


@app.get("/")
async def root():
    return {"message": "지켜봄 서비스 API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting 지켜봄 서비스...")
    # host를 '0.0.0.0'으로 설정하여 외부 접속 허용
    uvicorn.run(app, host="0.0.0.0", port=8001) 