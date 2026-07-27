from fastapi import FastAPI
from app.database import connect_to_db, close_db_connection
from app.routers import webhook
from app import database_async
import logging
from app.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="LifelineOne IA Bot", version="1.0.0")

@app.on_event("startup")
def _validar_webhook_global_config() -> None:
    if settings.WEBHOOK_GLOBAL_ENABLED:
        if not settings.WEBHOOK_GLOBAL_URL:
            logger.error(
                "WEBHOOK_GLOBAL_ENABLED=true, mas WEBHOOK_GLOBAL_URL não está configurada. "
                "Configure a URL pública do webhook com o sufixo /webhook."
            )
        elif not settings.WEBHOOK_GLOBAL_URL.strip().endswith("/webhook"):
            logger.warning(
                "WEBHOOK_GLOBAL_URL deve terminar com /webhook. URL atual: %s",
                settings.WEBHOOK_GLOBAL_URL,
            )
    elif settings.WEBHOOK_GLOBAL_URL:
        logger.info(
            "WEBHOOK_GLOBAL_URL está definida, mas WEBHOOK_GLOBAL_ENABLED=false. "
            "Se você quer usar essa URL, habilite WEBHOOK_GLOBAL_ENABLED=true."
        )


async def startup_event():
    _validar_webhook_global_config()
    # Diagnóstico: verificar se DATABASE_URL está configurada e logar instrução clara se ausente
    if not settings.DATABASE_URL:
        logger.error(
            "DATABASE_URL não encontrada. Configure a variável de ambiente `DATABASE_URL` ou crie um arquivo .env na raiz com `DATABASE_URL=postgresql://user:senha@host/db`. "
            "Sem essa configuração a aplicação não conseguirá conectar ao PostgreSQL."
        )
    await connect_to_db()
    # Inicializa pool async de conexões (se DATABASE_URL estiver configurada)
    try:
        await database_async.init_db_pool()
    except Exception:
        # erro já logado em database_async; não bloquear startup
        pass

@app.on_event("shutdown")
async def shutdown_event():
    await close_db_connection()
    try:
        await database_async.close_db_pool()
    except Exception:
        pass

# Registra as rotas modularizadas
app.include_router(webhook.router)

@app.get("/")
def home():
    return {"status": "ok", "message": "Servidor LifelineOne rodando com sucesso!"}
