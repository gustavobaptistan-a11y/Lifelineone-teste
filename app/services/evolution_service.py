import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class EvolutionService:
    def __init__(self):
        self.api_key = settings.EVOLUTION_API_KEY
        self.api_url = settings.EVOLUTION_API_URL.rstrip("/")
        self.instance_name = settings.EVOLUTION_INSTANCE_NAME
        self.enabled = settings.EVOLUTION_SEND_ENABLED
        self.client = httpx.AsyncClient(headers=self._headers())

    def _headers(self) -> dict[str, str]:
        return {"apikey": self.api_key} if self.api_key else {}

    @staticmethod
    def _normalize_number(remote_jid: str) -> str:
        return remote_jid.split("@")[0] if "@" in remote_jid else remote_jid

    def _resolve_instance_name(self) -> str:
        return getattr(self, "instance", None) or self.instance_name or settings.EVOLUTION_INSTANCE_NAME

    async def create_instance(self, instance_name: str):
        try:
            response = await self.client.post(
                f"{self.api_url}/instance/create",
                json={"instanceName": instance_name, "integration": "WHATSAPP-BAILEYS"},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Erro ao criar instancia no Evolution Go: %s", exc.response.text)
            return None
        except Exception as exc:
            logger.error("Erro inesperado ao criar instancia no Evolution Go: %s", exc)
            return None

    async def get_qrcode(self, instance_name: str):
        try:
            response = await self.client.get(f"{self.api_url}/instance/{instance_name}/qrcode")
            response.raise_for_status()
            return response.content
        except httpx.HTTPStatusError as exc:
            logger.error("Erro ao obter QR Code no Evolution Go: %s", exc.response.text)
            return None
        except Exception as exc:
            logger.error("Erro inesperado ao obter QR Code no Evolution Go: %s", exc)
            return None

    async def send_message(self, instance_name: str, phone_number: str, message: str):
        if not settings.EVOLUTION_SEND_ENABLED:
            logger.info("Envio de mensagens desabilitado. Mensagem para %s: %s", phone_number, message)
            return {"status": "disabled"}

        try:
            response = await self.client.post(
                f"{self.api_url}/message/sendText/{instance_name}",
                json={
                    "number": phone_number,
                    "textMessage": {"text": message},
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Erro ao enviar mensagem no Evolution Go: %s", exc.response.text)
            return None
        except Exception as exc:
            logger.error("Erro inesperado ao enviar mensagem no Evolution Go: %s", exc)
            return None

    async def send_text_message(self, remote_jid: str, text: str):
        if not getattr(self, "enabled", settings.EVOLUTION_SEND_ENABLED):
            logger.info("Envio de mensagens desabilitado. Mensagem para %s: %s", remote_jid, text)
            return {"status": "desabilitado"}

        instance_name = self._resolve_instance_name()
        api_key = getattr(self, "api_key", "") or settings.EVOLUTION_API_KEY
        if not instance_name or not api_key:
            logger.error("Evolution habilitada, mas EVOLUTION_INSTANCE_NAME ou EVOLUTION_API_KEY nao foram configurados")
            return {"status": "erro", "motivo": "configuracao_incompleta"}

        payload = {
            "number": self._normalize_number(remote_jid),
            "text": text,
        }
        headers = {"apikey": api_key}
        url = f"{self.api_url}/message/sendText/{instance_name}"

        try:
            async with httpx.AsyncClient(headers=headers) as client:
                response = await client.post(url, json=payload, headers=headers)
                if getattr(response, "is_error", False):
                    logger.error("Evolution retornou erro HTTP ao enviar texto: %s", getattr(response, "status_code", None))
                    return {"status": "erro", "http_status": getattr(response, "status_code", None)}
                return {"status": "enviado", "http_status": getattr(response, "status_code", None)}
        except Exception as exc:
            logger.error("Erro ao enviar texto via Evolution: %s", exc)
            return {"status": "erro", "motivo": "falha_requisicao"}


evolution_service = EvolutionService()