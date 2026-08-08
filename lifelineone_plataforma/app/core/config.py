from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Lifeline One - Plataforma e AI Orchestrator"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite+aiosqlite:///./lifeline_plataforma.db"

    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()
