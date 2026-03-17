"""
应用配置 — 从 .env 环境变量加载
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """全局配置项，由 .env 驱动"""

    # --- 应用 ---
    APP_NAME: str = "掘进工作面规程智能生成平台"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-to-a-random-secret-key-at-least-32-chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # --- 数据库 ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/excavation_platform"

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- 文件存储 ---
    OSS_ENDPOINT: str = ""
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET_NAME: str = "excavation-platform"

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # --- AI / LLM ---
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    AI_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 全局单例
settings = Settings()
