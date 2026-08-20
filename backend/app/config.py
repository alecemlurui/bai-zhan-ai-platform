"""
config.py

项目配置与 Tortoise ORM 配置。
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """环境变量配置。"""

    # App
    APP_NAME: str = "百战智能运营平台"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite://db.sqlite3"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXP_SECONDS: int = 3600

    # LLM
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_MODEL: str = "deepseek-chat"
    LLM_MOCK: bool = False
    LLM_TIMEOUT: int = 60
    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_BACKOFF: float = 2.0
    LLM_INPUT_PRICE_PER_1M: float = 0.0
    LLM_OUTPUT_PRICE_PER_1M: float = 0.0

    # OSS / Upload
    OSS_ENDPOINT: str = ""
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET: str = ""
    UPLOADER_MODE: str = "local"  # local | oss

    # Image generation
    IMAGE_GENERATOR_MODE: str = "mock"  # mock | remote | sd
    IMAGE_API_URL: str = ""
    IMAGE_API_KEY: str = ""
    IMAGE_MODEL: str = ""
    IMAGE_TIMEOUT: int = 120

    # XiaoHongShu
    XIAOHONGSHU_APP_ID: str = ""
    XIAOHONGSHU_APP_SECRET: str = ""
    XIAOHONGSHU_MOCK: bool = True

    # RAG / Vector store / Embedding
    VECTOR_DB_TYPE: str = "chroma"  # chroma | faiss | weaviate | milvus
    VECTOR_DB_PATH: str = "./chroma_db"
    VECTOR_DB_URL: str = ""
    VECTOR_DB_API_KEY: str = ""
    EMBEDDING_MODEL_PATH: str = ""
    EMBEDDING_TOKENIZER_PATH: str = ""
    EMBEDDING_MOCK: bool = True
    EMBEDDING_VECTOR_SIZE: int = 512
    RAG_CHUNK_SIZE: int = 300
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 5

    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


SETTINGS = get_settings()


# Tortoise ORM 配置（FastAPI + Aerich 共用）
TORTOISE_ORM = {
    "connections": {"default": SETTINGS.DATABASE_URL},
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        }
    },
}

# Celery 配置
CELERY_CONFIG = {
    "broker_url": SETTINGS.REDIS_URL,
    "result_backend": SETTINGS.REDIS_URL,
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "Asia/Shanghai",
    "enable_utc": True,
}
