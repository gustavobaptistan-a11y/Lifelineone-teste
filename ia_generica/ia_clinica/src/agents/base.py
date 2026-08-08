from pathlib import Path
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
