from fastapi import FastAPI
from pydantic import BaseModel

#1. Inicializa o palicativo fastapi
app = FastAPI(title="Agente para Clinica", description="Uma API simples usando FastAPI", version="1.0.0")

#2. Define o modelo de dados JSON que sera enviado
class MensagemEntrada(BaseModel):
    telefone: str
    texto: str

#3. Rota teste simples (GET) para checar servidor esta no ar
@app.get("/")
def checar_status():
    return {"status": "online", "mensagem": "API rodando com sucesso"}

#4. Rota principal (POST) recebera os dados
@app.post("/webhook")
def receber_mensagem(dados: MensagemEntrada):
    print(f"Mensagem recebida de {dados.telefone}: {dados.texto}")

    #Resposta de teste simples (Eco)
    return {
        "status": "sucesso",
        "resposta": f"Mensagem recebida de {dados.telefone}: {dados.texto}"
    }