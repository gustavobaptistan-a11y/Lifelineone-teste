from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres_user:postgres_password@localhost:5432/clinica_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    OPENAI_API_KEY: str = "sua_chave_da_openai_aqui"

    model_config = SettingsConfigDict(
        env_ignore_empty=True,
        extra="ignore"
    )

settings = Settings()
