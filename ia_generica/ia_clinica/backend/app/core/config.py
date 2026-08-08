import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Lifeline One - IA Clínica"
    VERSION: str = "1.8.0"
    API_V1_STR: str = "/api/v1"
    
    # Banco de Dados Supabase Cloud PostgreSQL 17 (Leitura exclusiva via .env)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Chaves de API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EVOLUTION_API_URL: str = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
    EVOLUTION_API_KEY: str = os.getenv("EVOLUTION_API_KEY", "")
    
    DEFAULT_CLINIC_ID: str = os.getenv("DEFAULT_CLINIC_ID", "11111111-1111-1111-1111-111111111111")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
