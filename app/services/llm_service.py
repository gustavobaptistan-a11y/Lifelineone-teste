import json
import logging
from typing import Any

from app.config import settings

try:
    from openai import OpenAI as OpenAIClient
except Exception:  # pragma: no cover
    OpenAIClient = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Voce e um assistente interno de interpretacao que ajuda a extrair "
    "informacoes estruturadas das respostas do paciente. Para cada mensagem "
    "do paciente, responda apenas com um JSON valido contendo as chaves "
    "abaixo. Nao inclua explicacoes, comentarios ou texto fora do JSON."
)


class LLMService:
    def __init__(self) -> None:
        self.enabled = bool(settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"
        self._client: Any = None

        if self.enabled and OpenAIClient is not None:
            try:
                self._client = OpenAIClient(api_key=settings.OPENAI_API_KEY)
            except Exception:
                logger.exception("Falha ao inicializar o cliente OpenAI")
                self.enabled = False
        elif self.enabled:
            logger.warning("OpenAI nao esta disponivel; LLM desabilitado.")
            self.enabled = False

    def verificar_urgencia(self, texto_usuario: str) -> bool:
        """Verificacao local baseada em palavras-chave de urgencia."""
        texto = texto_usuario.lower()
        palavras_urgentes = [
            "socorro",
            "emergencia",
            "dor no peito",
            "falta de ar",
            "desmaio",
            "sangramento",
        ]
        return any(palavra in texto for palavra in palavras_urgentes)

    def gerar_resposta_contextual(
        self,
        estado_atual: str,
        texto_usuario: str,
        historico: list | None = None,
    ) -> str:
        """Gera respostas mockadas para testes locais e fallback."""
        respostas_mock = {
            "inicio": (
                "Ola! Seja muito bem-vindo(a) a Clinica Lifeline. Para "
                "comecarmos o seu atendimento, qual e o seu nome completo?"
            ),
            "coletar_name": (
                "Obrigado pelas informacoes. Poderia me descrever qual e o "
                "seu principal sintoma ou o motivo da sua consulta?"
            ),
            "coletar_sintoma": (
                "Compreendo perfeitamente. O atendimento sera na modalidade "
                "particular ou por convenio?"
            ),
            "coletar_convenio": (
                "Perfeito. E a sua primeira consulta com o nosso especialista "
                "ou trata-se de um retorno?"
            ),
            "coletar_primeira_consulta": (
                "Entendido. Qual periodo do dia voce prefere para o "
                "atendimento? Manha ou tarde?"
            ),
            "coletar_horario_preferencia": (
                "Horarios disponiveis:\n"
                "1. Amanha as 09:00\n"
                "2. Amanha as 14:30\n"
                "3. Depois de amanha as 10:00\n\n"
                "Digite o numero da opcao desejada:"
            ),
            "finalizado": (
                "Consulta agendada com sucesso! Enviamos os detalhes para "
                "voce. Esperamos sua visita!"
            ),
        }

        resposta_padrao = (
            f"Recebido: '{texto_usuario}'. "
            "Vamos prosseguir para a proxima etapa."
        )

        return respostas_mock.get(estado_atual, resposta_padrao)

    def extract_structured(
        self,
        estado_atual: str,
        texto_usuario: str,
    ) -> dict:
        """
        Extrai dados estruturados usando o cliente de LLM se habilitado.

        Retorna um dicionario com pelo menos:
        - dados_extraidos: dict
        - urgente: bool
        """
        if not getattr(self, "enabled", False) or self._client is None:
            return {"dados_extraidos": {}, "urgente": False}

        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            "Formato JSON esperado:\n"
            "{\n"
            "  \"dados_extraidos\": {\n"
            "    \"nome\": \"string\",\n"
            "    \"sintoma\": \"string\",\n"
            "    \"convenio\": \"string\",\n"
            "    \"primeira_consulta\": \"Sim|Nao\",\n"
            "    \"preferencia_periodo\": \"manha|tarde\",\n"
            "    \"horario\": \"string\",\n"
            "    \"escolha\": \"1|2|3\"\n"
            "  },\n"
            "  \"urgente\": false\n"
            "}\n"
            "Se nao for possivel extrair algum campo, deixe-o como string "
            "vazia ou nao o inclua.\n"
            f"Estado atual: {estado_atual}\n"
            f"Mensagem do paciente: {texto_usuario}"
        )

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=250,
            )

            content = None
            if hasattr(response, "choices") and len(response.choices) > 0:
                choice = response.choices[0]
                if hasattr(choice, "message") and hasattr(
                    choice.message,
                    "content",
                ):
                    content = choice.message.content
                elif hasattr(choice, "text"):
                    content = choice.text

            if not content:
                return {"dados_extraidos": {}, "urgente": False}

            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                return {"dados_extraidos": {}, "urgente": False}

            return parsed
        except Exception:
            logger.exception("Erro ao extrair dados estruturados com LLM")
            self.enabled = False
            self._client = None
            return {"dados_extraidos": {}, "urgente": False}


llm_service = LLMService()
