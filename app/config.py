import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EVOLUTION_API_URL: str = os.getenv("EVOLUTION_API_URL", "https://api-wpp.ghosthub.com.br")
    EVOLUTION_API_KEY: str = os.getenv("EVOLUTION_API_KEY", "")
    EVOLUTION_INSTANCE: str = os.getenv("EVOLUTION_INSTANCE", "lifeline")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
