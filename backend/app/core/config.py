from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Application
    APP_NAME: str = "TeamFlow AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/teamflow_ai.db"
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # GitHub OAuth
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/github/callback"
    
    # Gemini AI (primary LLM)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # OpenAI (optional fallback)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    
    # Embedding model
    EMBEDDING_MODEL: str = "models/gemini-embedding-2"
    
    # Vector DB
    VECTOR_DB_TYPE: str = "chromadb"  # chromadb or pinecone
    CHROMADB_PATH: str = "./data/chromadb"
    CHROMADB_URL: str = "http://localhost:8001"
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    PINECONE_INDEX_NAME: str = "teamflow-ai"
    
    # Code Parsing
    MAX_FILE_SIZE_MB: int = 10
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # RAG Settings
    TOP_K_RETRIEVAL: int = 5
    TOP_K_RERANKING: int = 3
    MIN_CONFIDENCE_SCORE: float = 0.6
    
    # Rate Limiting
    RATE_LIMIT_QUERIES_PER_DAY: dict = {
        "free": 100,
        "pro": 10000,
        "enterprise": 1000000,
    }
    
    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 100
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Sentry (Error Tracking)
    SENTRY_DSN: Optional[str] = None
    
    # Feature Flags
    ENABLE_GRAPHRAG: bool = False
    ENABLE_HALLUCINATION_CHECK: bool = True
    ENABLE_CONFIDENCE_SCORING: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
