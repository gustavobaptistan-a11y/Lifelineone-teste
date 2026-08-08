import os
import subprocess
import sys

print("==================================================")
print("🚀 CRIANDO E CONFIGURANDO O PROJETO (VERSÃO CORRIGIDA)")
print("==================================================")

# 1. Criar estrutura de diretórios (Clean Architecture)
print("\n[1/5] Criando estrutura de pastas...")
pastas = [
    'src/core', 'src/models', 'src/services', 'src/api', 
    'src/agents/prompts', 'src/agents/tools', 'src/static'
]
for p in pastas:
    os.makedirs(p, exist_ok=True)
    open(os.path.join(p, '__init__.py'), 'w', encoding='utf-8').close()
open('__init__.py', 'w', encoding='utf-8').close()

# 2. Escrever arquivos de configuração e dependências (Versões Compatíveis com Python 3.12)
print("\n[2/5] Escrevendo arquivos de configuração e dependências...")

# requirements.txt atualizado sem conflitos
with open('requirements.txt', 'w', encoding='utf-8') as f:
    f.write('''fastapi==0.110.0
uvicorn==0.28.0
pydantic==2.7.4
pydantic-settings==2.2.1
langchain==0.1.12
langchain-core==0.1.33
langchain-openai==0.1.0
redis==5.0.2
psycopg[binary]==3.1.18
sqlalchemy==2.0.28
python-dotenv==1.0.1
requests==2.31.0
jinja2==3.1.3
langsmith==0.1.83
''')

# docker-compose.yml
with open('docker-compose.yml', 'w', encoding='utf-8') as f:
    f.write('''services:
  postgres:
    image: postgres:15-alpine
    container_name: clinica_postgres
    restart: always
    environment:
      POSTGRES_USER: postgres_user
      POSTGRES_PASSWORD: postgres_password
      POSTGRES_DB: clinica_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: clinica_redis
    restart: always
    ports:
      - "6379:6379"

volumes:
  pgdata:
''')

# src/core/config.py
with open('src/core/config.py', 'w', encoding='utf-8') as f:
    f.write('''from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres_user:postgres_password@localhost:5432/clinica_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    OPENAI_API_KEY: str = "sua_chave_da_openai_aqui"

    model_config = SettingsConfigDict(
        env_ignore_empty=True,
        extra="ignore"
    )

settings = Settings()
''')

# src/core/database.py
with open('src/core/database.py', 'w', encoding='utf-8') as f:
    f.write('''from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from src.core.config import settings

engine = create_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
''')

# src/models/paciente.py
with open('src/models/paciente.py', 'w', encoding='utf-8') as f:
    f.write('''from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from src.core.database import Base

class PacienteModel(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(150), nullable=False)
    telefone = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    aceite_lgpd = Column(Boolean, default=False, nullable=False)
    data_aceite = Column(DateTime(timezone=True), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
''')

# src/core/init_db.py
with open('src/core/init_db.py', 'w', encoding='utf-8') as f:
    f.write('''from src.core.database import engine, Base
from src.models.paciente import PacienteModel

def init_db():
    print("Conectando ao banco de dados e criando as tabelas...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso!")

if __name__ == "__main__":
    init_db()
''')

# Prompts iniciais de Agentes
with open('src/agents/prompts/triagem.txt', 'w', encoding='utf-8') as f:
    f.write('Voce e o Agente de Triagem e Acolhimento de uma Clinica de Alergia. Seu objetivo e receber o paciente com extrema empatia, identificar sintomas iniciais de alergia e coletar o aceite da LGPD. Nunca invente diagnosticos medicos.')

with open('src/agents/prompts/supervisor.txt', 'w', encoding='utf-8') as f:
    f.write('Voce e o Agente Supervisor de uma Clinica de Alergia. Sua funcao e analisar a mensagem do paciente e decidir qual proximo passo tomar.')

# src/agents/base.py
with open('src/agents/base.py', 'w', encoding='utf-8') as f:
    f.write('''from pathlib import Path
from langchain_openai import ChatOpenAI
from src.core.config import settings

class BaseAgent:
    @staticmethod
    def carregar_prompt(nome_arquivo: str) -> str:
        caminho = Path(__file__).parent / "prompts" / f"{nome_arquivo}.txt"
        if not caminho.exists():
            return "Voce e um assistente util."
        return caminho.read_text(encoding="utf-8")

    @staticmethod
    def salvar_prompt(nome_arquivo: str, conteudo: str):
        caminho = Path(__file__).parent / "prompts" / f"{nome_arquivo}.txt"
        caminho.write_text(conteudo, encoding="utf-8")

    @classmethod
    def executar(cls, nome_agente: str, mensagem_usuario: str) -> str:
        system_prompt = cls.carregar_prompt(nome_agente)
        
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sua_chave_da_openai_aqui":
            return "[Modo Simulação] Insira sua OPENAI_API_KEY no config.py para usar a OpenAI real."

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=settings.OPENAI_API_KEY)
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=mensagem_usuario)
        ]
        resposta = llm.invoke(messages)
        return resposta.content
''')

# src/api/painel.py
with open('src/api/painel.py', 'w', encoding='utf-8') as f:
    f.write('''from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import os

router = APIRouter()

@router.get("/painel", response_class=HTMLResponse)
def painel_refinamento(request: Request):
    prompts_dir = os.path.join("src", "agents", "prompts")
    arquivos = [f.replace(".txt", "") for f in os.listdir(prompts_dir) if f.endswith(".txt")]
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Painel de Refinamento de IAs - Clinica</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
            .container {{ max-width: 1000px; margin: auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }}
            h1 {{ color: #38bdf8; text-align: center; margin-bottom: 30px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .card {{ background: #0f172a; padding: 20px; border-radius: 8px; border: 1px solid #334155; }}
            label {{ display: block; margin-bottom: 8px; font-weight: 600; color: #94a3b8; }}
            select, textarea, input[type="text"] {{ width: 100%; padding: 12px; background: #1e293b; border: 1px solid #475569; color: #fff; border-radius: 6px; margin-bottom: 15px; font-size: 14px; box-sizing: border-box; }}
            textarea {{ height: 220px; resize: vertical; font-family: monospace; }}
            button {{ background: #0284c7; color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; transition: background 0.2s; }}
            button:hover {{ background: #0ea5e9; }}
            .chat-box {{ height: 180px; background: #1e293b; border: 1px solid #475569; border-radius: 6px; padding: 10px; overflow-y: auto; margin-bottom: 15px; font-size: 13px; }}
            .msg-user {{ color: #38bdf8; margin-bottom: 8px; }}
            .msg-ai {{ color: #4ade80; margin-bottom: 8px; }}
        </style>
        <script>
            async function carregarPrompt() {{
                const agente = document.getElementById("agente_select").value;
                const response = await fetch(`/api/prompt/${{agente}}`);
                const data = await response.json();
                document.getElementById("conteudo_prompt").value = data.prompt;
            }}

            async function salvarPrompt(event) {{
                event.preventDefault();
                const agente = document.getElementById("agente_select").value;
                const conteudo = document.getElementById("conteudo_prompt").value;
                
                await fetch(`/api/prompt/${{agente}}`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ conteudo }})
                }});
                alert("Prompt refinado e salvo com sucesso!");
            }}

            async function testarIA(event) {{
                event.preventDefault();
                const agente = document.getElementById("agente_select").value;
                const mensagem = document.getElementById("mensagem_teste").value;
                
                const chatBox = document.getElementById("chat_box");
                chatBox.innerHTML += `<div class="msg-user"><b>Você:</b> ${{mensagem}}</div>`;
                
                const response = await fetch('/api/testar', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ agente, mensagem }})
                }});
                const data = await response.json();
                
                chatBox.innerHTML += `<div class="msg-ai"><b>IA (${{agente}}):</b> ${{data.resposta}}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
                document.getElementById("mensagem_teste").value = "";
            }}
        </script>
    </head>
    <body onload="carregarPrompt()">
        <div class="container">
            <h1>🎛️ Painel Avançado de Refinamento de Agentes</h1>
            <div style="margin-bottom: 20px;">
                <label>Selecione o Agente para Calibrar:</label>
                <select id="agente_select" onchange="carregarPrompt()">
                    {''.join([f'<option value="{a}">{a.capitalize()}</option>' for a in arquivos])}
                </select>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>📝 Editor de System Prompt</h3>
                    <form onsubmit="salvarPrompt(event)">
                        <label>Instrução Comportamental:</label>
                        <textarea id="conteudo_prompt"></textarea>
                        <button type="submit">💾 Salvar Refinamento</button>
                    </form>
                </div>
                <div class="card">
                    <h3>💬 Simulador de Atendimento</h3>
                    <div id="chat_box" class="chat-box"></div>
                    <form onsubmit="testarIA(event)">
                        <input type="text" id="mensagem_teste" placeholder="Digite uma mensagem..." required>
                        <button type="submit" style="background: #16a34a;">⚡ Testar Resposta da IA</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content
''')

# src/api/main.py
with open('src/api/main.py', 'w', encoding='utf-8') as f:
    f.write('''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.api.painel import router as painel_router
from src.agents.base import BaseAgent

app = FastAPI(title="Clinica Alergia IA - API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(painel_router)

class PromptUpdate(BaseModel):
    conteudo: str

class TesteRequest(BaseModel):
    agente: str
    mensagem: str

@app.get("/api/prompt/{nome_agente}")
def get_prompt(nome_agente: str):
    prompt = BaseAgent.carregar_prompt(nome_agente)
    return {"prompt": prompt}

@app.post("/api/prompt/{nome_agente}")
def update_prompt(nome_agente: str, data: PromptUpdate):
    BaseAgent.salvar_prompt(nome_agente, data.conteudo)
    return {"status": "sucesso", "mensagem": f"Prompt atualizado."}

@app.post("/api/testar")
def testar_agente(data: TesteRequest):
    resposta = BaseAgent.executar(data.agente, data.mensagem)
    return {"resposta": resposta}

@app.get("/")
def root():
    return {"mensagem": "API operando! Acesse o painel em /painel"}
''')

# 3. Instalar dependências Python
print("\n[3/5] Instalando dependências e atualizando pip...")
subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)

# 4. Subir containers do Docker
print("\n[4/5] Subindo containers do Docker Compose...")
subprocess.run(["docker", "compose", "up", "-d"], check=True)

# 5. Criar tabelas no banco de dados
print("\n[5/5] Inicializando as tabelas no banco de dados...")
subprocess.run([sys.executable, '-m', 'src.core.init_db'], check=True)

print("\n==================================================")
print("✨ TUDO PRONTO E CONFIGURADO COM SUCESSO! ✨")
print("==================================================")
print("Para rodar o servidor, digite:")
print("   python -m uvicorn src.api.main:app --reload")
print("Em seguida abra: http://localhost:8000/painel")