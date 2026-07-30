import logging
from pathlib import Path

from fastapi import FastAPI

from app import database_async
from app.config import settings
from app.database import close_db_connection, connect_to_db
from app.routers import webhook
from app.routers.admin import router as admin_router
from app.routers.dashboard import router as dashboard_router

logger = logging.getLogger(__name__)

app = FastAPI(title="LifelineOne IA Bot", version="1.0.0")


@app.on_event("startup")
def _validar_webhook_global_config() -> None:
    if settings.WEBHOOK_GLOBAL_ENABLED:
        if not settings.WEBHOOK_GLOBAL_URL:
            logger.error(
                "WEBHOOK_GLOBAL_ENABLED=true, mas WEBHOOK_GLOBAL_URL nao esta "
                "configurada. Configure a URL publica do webhook com o sufixo "
                "/webhook."
            )
        elif not settings.WEBHOOK_GLOBAL_URL.strip().endswith("/webhook"):
            logger.warning(
                "WEBHOOK_GLOBAL_URL deve terminar com /webhook. URL atual: %s",
                settings.WEBHOOK_GLOBAL_URL,
            )
    elif settings.WEBHOOK_GLOBAL_URL:
        logger.info(
            "WEBHOOK_GLOBAL_URL esta definida, mas "
            "WEBHOOK_GLOBAL_ENABLED=false. "
            "Se voce quer usar essa URL, habilite WEBHOOK_GLOBAL_ENABLED=true."
        )


async def startup_event():
    _validar_webhook_global_config()
    if not settings.DATABASE_URL:
        logger.error(
            "DATABASE_URL nao encontrada. Configure a variavel de ambiente "
            "`DATABASE_URL` ou crie um arquivo .env na raiz com "
            "`DATABASE_URL=postgresql://user:senha@host/db`. Sem essa "
            "configuracao a aplicacao nao conseguira conectar ao PostgreSQL."
        )
    await connect_to_db()
    try:
        await database_async.init_db_pool()
    except Exception:
        pass


@app.on_event("shutdown")
async def shutdown_event():
    await close_db_connection()
    try:
        await database_async.close_db_pool()
    except Exception:
        pass


app.include_router(webhook.router)
app.include_router(dashboard_router)
app.include_router(admin_router)


@app.get("/health")
def health():
    evolution_configured = bool(
        settings.EVOLUTION_API_URL
        and settings.EVOLUTION_API_KEY
        and settings.EVOLUTION_INSTANCE_NAME
    )
    calendar_credentials_configured = any(
        Path(path).exists()
        for path in [
            settings.GOOGLE_CREDENTIALS_FILE,
            settings.GOOGLE_TOKEN_FILE,
        ]
        if path
    )

    return {
        "status": "ok",
        "service": "lifeline-bot",
        "integrations": {
            "database": {"configured": bool(settings.DATABASE_URL)},
            "redis": {
                "enabled": settings.REDIS_ENABLED,
                "configured": bool(settings.REDIS_URL),
            },
            "evolution": {
                "send_enabled": settings.EVOLUTION_SEND_ENABLED,
                "configured": evolution_configured,
                "ready_for_send": bool(
                    settings.EVOLUTION_SEND_ENABLED and evolution_configured
                ),
            },
            "openai": {"configured": bool(settings.OPENAI_API_KEY)},
            "google_calendar": {
                "enabled": settings.GOOGLE_CALENDAR_ENABLED,
                "credentials_configured": calendar_credentials_configured,
                "local_oauth_allowed": (
                    settings.GOOGLE_CALENDAR_ALLOW_LOCAL_AUTH
                ),
            },
        },
    }


@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "Servidor LifelineOne rodando com sucesso!",
    }
