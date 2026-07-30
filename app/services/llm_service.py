import json
import logging

from app.config import settings

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Você é um assistente de interpretação interno que ajuda a extrair informações estruturadas das respostas do paciente. "
    "Para cada mensagem do paciente, responda apenas com um JSON válido contendo as chaves abaixo." 
    "Não inclua explicações, comentários ou texto fora do JSON."
)

class LLMService:
    def __init__(self):
        self.enabled = bool(settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"
        self._client = None

        if self.enabled and OpenAI is not None:
            try:
                self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception:
                logger.exception("Falha ao inicializar o cliente OpenAI")
                self.enabled = False
        elif self.enabled:
            logger.warning("OpenAI não está disponível; LLM desabilitado.")
            self.enabled = False

    def verificar_urgencia(self, texto_usuario: str) -> bool:
        """
        Verificação local simulada baseada em palavras-chave de urgência.
        """
        texto = texto_usuario.lower()
        palavras_urgentes = ["socorro", "emergência", "dor no peito", "falta de ar", "desmaio", "sangramento"]
        return any(p in texto for p in palavras_urgentes)

    def gerar_resposta_contextual(self, estado_atual: str, texto_usuario: str, historico: list = None) -> str:
        """
        Gera respostas imaginárias e contextuais baseadas puramente no estado atual.
        """
        respostas_mock = {
            "inicio": "Olá! Seja muito bem-vindo(a) à Clínica Lifeline. Para começarmos o seu atendimento, qual é o seu nome completo?",
            "coletar_name": f"Obrigado pelas informações. Poderia me descrever qual é o seu principal sintoma ou o motivo da sua consulta?",
            "coletar_sintoma": "Compreendo perfeitamente. O atendimento será na modalidade Particular ou por Convênio?",
            "coletar_convenio": "Perfeito. É a sua primeira consulta com o nosso especialista ou trata-se de um retorno?",
            "coletar_primeira_consulta": "Entendido. Qual período do dia você prefere para o atendimento? (Manhã ou Tarde)",
            "coletar_horario_preferencia": (
                "📋 **Horários disponíveis:**\n"
                "1️⃣ Amanhã às 09:00\n"
                "2️⃣ Amanhã às 14:30\n"
                "3️⃣ Depois de amanhã às 10:00\n\n"
                "Digite o número da opção desejada:"
            ),
            "finalizado": "✅ **Consulta agendada com sucesso!** Enviamos os detalhes para você. Esperamos sua visita!"
        }

        return respostas_mock.get(estado_atual, f"Recebido: '{texto_usuario}'. Vamos prosseguir para a próxima etapa.")

    def extract_structured(self, estado_atual: str, texto_usuario: str) -> dict:
        """
        Extrai dados estruturados usando o cliente de LLM se habilitado.

        Retorna um dicionário com pelo menos:
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
            "Se não for possível extrair algum campo, deixe-o como string vazia ou não o inclua.\n"
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
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
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
