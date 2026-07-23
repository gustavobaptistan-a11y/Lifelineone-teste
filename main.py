from fastapi import FastAPI
from app.database import connect_to_db, close_db_connection
from app.routers import webhook

app = FastAPI(title="LifelineOne IA Bot", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    await connect_to_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db_connection()

# Registra as rotas modularizadas
app.include_router(webhook.router)

@app.get("/")
def home():
    return {"status": "ok", "message": "Servidor LifelineOne rodando com sucesso!"}
