import os
import sys
import datetime
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Adicionar backend ao sys.path se necessário
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.api.v1.webhooks.router import router as webhooks_router
from app.api.v1.clinics.router import router as clinics_router

logger = logging.getLogger(__name__)

app = FastAPI(title="VittaMed Clinical Hub - Lifeline One", version="1.8")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhooks_router, prefix="/api/v1/webhooks", tags=["Webhooks"])
app.include_router(clinics_router, prefix="/api/v1/clinics", tags=["Clinics"])

# In-Memory Store de IAs Registradas para Treinamento Multi-Agentes
AGENTS_STORE: List[Dict[str, Any]] = [
    {
        "id": "agent-roberta",
        "nome": "IA Roberta",
        "funcao": "Recepção, Triagem & Agendamentos",
        "tom_de_voz": "Ultra-Humano, Empático e Acolhedor",
        "modelo": "GPT-4o Mini",
        "status": "Ativo"
    },
    {
        "id": "agent-drai",
        "nome": "Copiloto IA Médico (Dr. AI)",
        "funcao": "Apoio a Anamnese & Transcrição Clínica",
        "tom_de_voz": "Técnico, Preciso e Médico",
        "modelo": "GPT-4o",
        "status": "Ativo"
    },
    {
        "id": "agent-triagem",
        "nome": "IA Triagem Telefônica",
        "funcao": "Triagem Rápida de Sintomas por Voz",
        "tom_de_voz": "Objetivo e Focado em Emergência",
        "modelo": "GPT-4o Mini",
        "status": "Ativo"
    }
]

# In-memory feedback storage por Agente
FEEDBACK_STORE: List[Dict[str, Any]] = [
    {
        "id": "fb-001",
        "agente_id": "agent-roberta",
        "agente_nome": "IA Roberta",
        "data": "Hoje às 17:35",
        "categoria": "Tom de Voz & Empatia",
        "avaliacao": "5",
        "estrelas": "⭐⭐⭐⭐⭐ (5/5)",
        "comentario": "Adorei a velocidade de resposta! Manter sempre a oferta do café quentinho na recepção.",
        "status": "Aplicado",
        "badge_class": "badge-status-green"
    },
    {
        "id": "fb-002",
        "agente_id": "agent-roberta",
        "agente_nome": "IA Roberta",
        "data": "Hoje às 17:28",
        "categoria": "Convênios & Preços",
        "avaliacao": "4",
        "estrelas": "⭐⭐⭐⭐ (4/5)",
        "comentario": "Confirmar se aceitamos consulta com recibo para reembolso do Bradesco.",
        "status": "Aplicado",
        "badge_class": "badge-status-green"
    }
]


@app.get("/api/v1/agents")
async def list_agents():
    return {"agents": AGENTS_STORE}


@app.post("/api/v1/agents")
async def create_agent(payload: Dict[str, Any] = Body(...)):
    new_agent = {
        "id": f"agent-{len(AGENTS_STORE) + 1:03d}",
        "nome": payload.get("nome", "Nova IA"),
        "funcao": payload.get("funcao", "Atendimento Especializado"),
        "tom_de_voz": payload.get("tom_de_voz", "Acolhedor"),
        "modelo": payload.get("modelo", "GPT-4o Mini"),
        "status": "Ativo"
    }
    AGENTS_STORE.append(new_agent)
    return {"status": "success", "message": f"Agente '{new_agent['nome']}' cadastrado para treinamento e refinamento!", "agent": new_agent}


@app.get("/api/v1/feedback")
async def get_feedbacks():
    return {"feedbacks": FEEDBACK_STORE}


@app.post("/api/v1/feedback")
async def create_feedback(payload: Dict[str, Any] = Body(...)):
    now_str = datetime.datetime.now().strftime("Hoje às %H:%M")
    rating_val = str(payload.get("rating", "5"))
    agente_id = payload.get("agente_id", "agent-roberta")
    agente_nome = "IA Roberta"
    for a in AGENTS_STORE:
        if a["id"] == agente_id:
            agente_nome = a["nome"]

    stars_map = {
        "5": "⭐⭐⭐⭐⭐ (5/5)",
        "4": "⭐⭐⭐⭐ (4/5)",
        "3": "⭐⭐⭐ (3/5)",
        "2": "⭐⭐ (2/5)",
        "1": "⭐ (1/5)"
    }
    fb_item = {
        "id": f"fb-{len(FEEDBACK_STORE) + 1:03d}",
        "agente_id": agente_id,
        "agente_nome": agente_nome,
        "data": now_str,
        "categoria": payload.get("category", "Geral"),
        "avaliacao": rating_val,
        "estrelas": stars_map.get(rating_val, "⭐⭐⭐⭐⭐"),
        "comentario": payload.get("comment", ""),
        "status": "Pendente",
        "badge_class": "badge-status-blue"
    }
    FEEDBACK_STORE.insert(0, fb_item)
    return {"status": "success", "message": f"Sugestão para {agente_nome} registrada!", "item": fb_item}


@app.post("/api/v1/feedback/{feedback_id}/apply")
async def apply_feedback(feedback_id: str):
    for item in FEEDBACK_STORE:
        if item["id"] == feedback_id:
            item["status"] = "Aplicado"
            item["badge_class"] = "badge-status-green"
            return {"status": "success", "message": f"Sugestão {feedback_id} aplicada ao treinamento do agente {item['agente_nome']}!", "item": item}
    return {"status": "error", "message": "Feedback não encontrado."}


frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    @app.get("/painel")
    @app.get("/chefe")
    @app.get("/demo")
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
