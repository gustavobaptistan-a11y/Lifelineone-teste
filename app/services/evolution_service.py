import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

class EvolutionService:
    def __init__(self):
        self.base_url = settings.EVOLUTION_API_URL.rstrip("/")
        self.api_key = settings.EVOLUTION_API_KEY
        self.instance = settings.EVOLUTION_INSTANCE
        self.enabled = settings.EVOLUTION_SEND_ENABLED

    async def send_text_message(self, phone: str, text: str) -> dict:
        if not self.enabled:
            return {"status": "desabilitado"}

        if not self.api_key or not self.instance:
            return {"status": "erro", "motivo": "configuracao da Evolution incompleta"}

        number = phone.split("@", 1)[0].split(":", 1)[0]
        url = f"{self.base_url}/message/sendText/{self.instance}"
        headers = {
            "Content-Type": "application/json",
            "apikey": self.api_key
        }
        payload = {
            "number": number,
            "text": text
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)

                if response.is_error:
                    logger.warning("Evolution retornou HTTP %s", response.status_code)
                    return {"status": "erro", "http_status": response.status_code}

                return {"status": "enviado", "http_status": response.status_code}
        except httpx.HTTPError:
            logger.exception("Falha de comunicacao com a Evolution API")
            return {"status": "erro", "motivo": "falha de comunicacao"}

evolution_service = EvolutionService()
