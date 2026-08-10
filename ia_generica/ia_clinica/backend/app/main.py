import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.api.v1.webhooks.router import router as webhooks_router
from app.api.v1.clinics.router import router as clinics_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir Roteadores da API V1
app.include_router(webhooks_router, prefix=f"{settings.API_V1_STR}/webhooks", tags=["Webhooks"])
app.include_router(clinics_router, prefix=f"{settings.API_V1_STR}/clinics", tags=["Clinics"])

# Servir arquivos estáticos do Frontend
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir, html=True), name="static")

    @app.get("/")
    @app.get("/index.html")
    @app.get("/static/index.html")
    @app.get("/painel")
    @app.get("/clinical")
    @app.get("/clinical/configuracoes")
    @app.get("/clinical/configuracoes/")
    async def serve_index():
        index_path = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"status": "online", "message": "Lifeline One API Operacional"}

    @app.get("/style.css")
    @app.get("/clinical/style.css")
    @app.get("/clinical/configuracoes/style.css")
    async def serve_css():
        return FileResponse(os.path.join(frontend_dir, "style.css"))

    @app.get("/app.js")
    @app.get("/clinical/app.js")
    @app.get("/clinical/configuracoes/app.js")
    async def serve_js():
        return FileResponse(os.path.join(frontend_dir, "app.js"))
else:
    @app.get("/")
    async def root():
        return {"status": "online", "message": "Lifeline One API Operacional"}
