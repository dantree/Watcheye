from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 기본 설정
    APP_NAME: str = "지켜봄 서비스"
    DEBUG: bool = True
    
    # SQLite 사용을 위한 데이터베이스 설정
    DATABASE_URL: str = "sqlite:///./zikeobom.db"
    
    # AI 모델 설정
    MODEL_PATH: str = "models/"
    DETECTION_THRESHOLD: float = 0.5
    
    class Config:
        env_file = ".env"

settings = Settings() 