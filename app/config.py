from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://legalai:legalai123@localhost:5432/legalai"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Google Drive
    GOOGLE_DRIVE_CREDENTIALS_PATH: str = "./credentials/google-credentials.json"
    GOOGLE_DRIVE_TOKEN_PATH: str = "./credentials/token.json"
    SENTENCIAS_FILE_ID: str = "1yNAwckn4rPnlpSgmW-xyB10WL4CcgRvE"
    ESCRITOS_FOLDER_ID: str = "1hzAIv5AJWGI8Q76M4IjI0k4ZFXw8UBeu"
    
    # AI Models
    MODEL_PATH: str = "./models"
    VECTOR_DB_PATH: str = "./vector_db"
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    LLM_MODEL: str = "microsoft/DialoGPT-medium"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Legal AI"
    VERSION: str = "1.0.0"
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    
    # File upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "./uploads"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Ensure directories exist
os.makedirs(settings.MODEL_PATH, exist_ok=True)
os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs("./credentials", exist_ok=True)