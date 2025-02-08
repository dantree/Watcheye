from fastapi import FastAPI, Depends
from loguru import logger
from .api.endpoints import events, cameras, views, system, login, register
from .models.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware

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
app.include_router(views.router) 

app.include_router(
    login.router,
    prefix="/api",
    tags=["auth"]
)

app.include_router(
    register.router,
    prefix="/api",
    tags=["auth"]
)

app.include_router(
    cameras.router,
    prefix="/api/v1",
    tags=["cameras"],
    # dependencies=[Depends(get_current_user)]
)
app.include_router(
    events.router,
    prefix="/api/v1",
    tags=["events"],
    # dependencies=[Depends(get_current_user)]
)
app.include_router(
    system.router,
    prefix="/api/v1",
    tags=["system"],
    # dependencies=[Depends(get_current_user)]
)

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