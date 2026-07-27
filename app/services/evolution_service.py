import httpx
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class EvolutionService:
    def __init__(self):
        self.api_key = settings.EVOLUTION_API_KEY
        self.api_url = settings.EVOLUTION_API_URL
        self.client = httpx.AsyncClient(headers={"apikey": self.api_key})

    async def create_instance(self, instance_name: str):
        """
        Cria uma nova instância no Evolution Go.
        """
        try:
            response = await self.client.post(
                f"{self.api_url}/instance/create",
                json={"instanceName": instance_name, "integration": "WHATSAPP-BAILEYS"},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro ao criar instância no Evolution Go: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao criar instância no Evolution Go: {e}")
            return None

    async def get_qrcode(self, instance_name: str):
        """
        Obtém o QR Code para conectar a instância.
        """
        try:
            response = await self.client.get(
                f"{self.api_url}/instance/{instance_name}/qrcode",
            )
            response.raise_for_status()
            return response.content
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro ao obter QR Code no Evolution Go: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao obter QR Code no Evolution Go: {e}")
            return None

    async def send_message(self, instance_name: str, phone_number: str, message: str):
        """
        Envia uma mensagem de texto.
        """
        if not settings.EVOLUTION_SEND_ENABLED:
            logger.info(f"Envio de mensagens desabilitado. Mensagem para {phone_number}: {message}")
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
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro ao enviar mensagem no Evolution Go: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar mensagem no Evolution Go: {e}")
            return None

    async def send_text_message(self, remote_jid: str, text: str):
        """
        Compat layer usada pelo resto da aplicação/tests: normaliza JID e envia texto.
        Retorna dicionários em português conforme os testes.
        """
        if not getattr(self, "enabled", settings.EVOLUTION_SEND_ENABLED):
            logger.info(f"Envio de mensagens desabilitado. Mensagem para {remote_jid}: {text}")
            return {"status": "desabilitado"}

        number = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid

        payload = {"number": number, "text": text}

        try:
            async with httpx.AsyncClient(headers={"apikey": getattr(self, "api_key", self.api_key)}) as client:
                url = f"{self.api_url}/message/sendText/{getattr(self, 'instance', '')}"
                response = await client.post(url, json=payload, headers={"apikey": getattr(self, "api_key", self.api_key)})
                return {"status": "enviado", "http_status": getattr(response, "status_code", None)}
        except Exception as e:
            logger.error(f"Erro ao enviar texto via Evolution: {e}")
            return None
evolution_service = EvolutionService()
