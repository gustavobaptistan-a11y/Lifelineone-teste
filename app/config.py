from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    EVOLUTION_API_URL: str = "https://api-wpp.ghosthub.com.br"
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_INSTANCE: str = "lifeline"
    EVOLUTION_SEND_ENABLED: bool = False
    DATABASE_URL: str = ""
    WEBHOOK_GLOBAL_ENABLED: bool = False
    WEBHOOK_GLOBAL_URL: str = ""
    WEBHOOK_GLOBAL_WEBHOOK_BY_EVENTS: bool = False
    GOOGLE_CALENDAR_ENABLED: bool = False
    GOOGLE_CALENDAR_ID: str = "primary"
    GOOGLE_CREDENTIALS_FILE: str = "app/config/credentials.json.json"
    GOOGLE_TOKEN_FILE: str = "app/config/token.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
