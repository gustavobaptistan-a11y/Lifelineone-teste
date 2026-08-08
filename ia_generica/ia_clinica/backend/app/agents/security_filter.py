import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class SecurityFilterAgent:
    """
    Agente de Filtro de Segurança & Guardrails Avançado.
    - Bloqueia Prompt Injections ("ignore instruções anteriores", "mostre a API key").
    - Intercepta Emergências Médicas (Encaminhamento para Pronto-Socorro).
    - Impede Prescrição Médica Direta ou Medicamentos Tarja Preta sem Consulta.
    - Bloqueia Vazamento de Dados Sensíveis e Credenciais de Sistema.
    """

    def check_message_security(self, content: str) -> Tuple[bool, bool, str]:
        low = content.lower()

        # 1. Tentativas de Prompt Injection ou Vazamento de Credenciais
        injection_terms = [
            "ignore previous instructions", "ignore as instruçoes", "ignore as instrucoes",
            "mostre o prompt", "qual a sua api key", "qual a senha do banco",
            "database_url", "supabase_key", "openai_api_key", "system prompt", "reveal key"
        ]
        if any(term in low for term in injection_terms):
            logger.warning(f"Tentativa de Prompt Injection ou Vazamento de Chaves bloqueada: {content[:30]}...")
            return False, False, "Tentativa de Violação de Segurança Identificada"

        # 2. Palavras de Emergência Médica Grave
        emergency_terms = [
            "falta de ar severa", "anaphylaxis", "choque anafilatico", "parada respiratoria",
            "desmaiou", "inconsciente", "sem respirar", "edema de glote"
        ]
        if any(term in low for term in emergency_terms):
            return False, True, "Emergência Médica Detectada"

        # 3. Prescrição Indevida de Remédios Tarja Preta ou Dosagens Sem Avaliação
        pharma_terms = ["me receite", "prescreva remedio", "qual a dose de corticoide", "posso tomar 50mg"]
        if any(term in low for term in pharma_terms):
            return False, False, "Solicitação Indevida de Prescrição Direta"

        return True, False, "Mensagem Segura"


security_filter_agent = SecurityFilterAgent()
